from typing import List, Dict, Optional
import time
import threading
import random
import os
from dataclasses import dataclass

from config_module import ParsedConfig, Burst
from packet_sender import get_packet_sender
from packet_sender.utils import check_interface_binding_permission
from ue_generator import UEProfile
from display import Display
from recorder import Recorder

class PoissonWaitGenerator:
    def __init__(self, 
                 arrival_rate, 
                 burst_config: Burst):
        self.default_rate = arrival_rate
        self.burst_enabled = burst_config.enabled

        if not self.burst_enabled:
            self.burst_chance = 0.0
            self.burst_rate = 0.0
            self.burst_on_min = 0.0
            self.burst_on_max = 0.0
            self.burst_off_min = 0.0
            self.burst_off_max = 0.0
            self.in_burst = False
            self.phase_end_time = time.time()
            return
        
        # 如果啟用了 burst，則從配置中讀取相關參數
        self.burst_chance = burst_config.burst_chance 
        self.burst_rate = burst_config.burst_arrival_rate
        self.burst_on_min = burst_config.burst_on_duration.min
        self.burst_on_max = burst_config.burst_on_duration.max
        self.burst_off_min = burst_config.burst_off_duration.min
        self.burst_off_max = burst_config.burst_off_duration.max
        self.in_burst = False
        self.phase_end_time = time.time()  # 用於追蹤當前階段的結束時間

    def next_wait(self):
        now = time.time()

        if self.burst_enabled:
            if now >= self.phase_end_time: # 切換狀態
                self.in_burst = random.random() < self.burst_chance
                duration = (random.uniform(self.burst_on_min, self.burst_on_max)
                            if self.in_burst else
                            random.uniform(self.burst_off_min, self.burst_off_max))
                self.phase_end_time = now + duration

            current_rate = self.burst_rate if self.in_burst else self.default_rate
        else: # 如果沒有啟用 burst，則使用默認速率
            current_rate = self.default_rate

        # 如果 current_rate 為 0，表示不該產生任何封包
        if current_rate <= 0:
            return float('inf')  # 等到世界末日
        return random.expovariate(current_rate)

class Simulator:
    def __init__(
        self,
        ue_profiles: List[UEProfile],
        cfg: ParsedConfig,
    ):
        # Thread Management Variables
        self.lock = threading.Lock()
        self.threads: List[threading.Thread] = []

        self.ue_profiles = ue_profiles
        self.duration = cfg.simulation.duration_sec
        self.target_ips = cfg.simulation.target_ips
        self.packet_type = cfg.simulation.packet_type
        self.start_time = time.time()
        self.end_time = self.start_time + self.duration
        self.recorder = Recorder(self.lock, self.ue_profiles, cfg.simulation.record_csv_path)
        self.display = Display(self.recorder, self.lock, cfg.simulation.display_interval_sec)
 
    def simulate_ue(self, ue: UEProfile):
        iface = f"uesimtun{ue.id}"
        if ue.packet_arrival_rate <= 0:
            print(f'[INFO] UE {ue.id} has a packet arrival rate of 0. Skipping simulation.')
            return

        # Get the packet sender based on the packet type and interface, ex: "pingSender", "tcpSender", "udpSender"
        try:
            packet_sender = get_packet_sender(self.packet_type, iface)
        except (PermissionError, OSError) as e:
            print(f'[ERROR] Failed to initialize packet sender for UE {ue.id}: {e}')
            print(f'[ERROR] UE {ue.id} simulation stopped.')
            return
        except Exception as e:
            print(f'[ERROR] Unexpected error initializing packet sender for UE {ue.id}: {e}')
            print(f'[ERROR] UE {ue.id} simulation stopped.')
            return
        waiting_timer = PoissonWaitGenerator(
            arrival_rate=ue.packet_arrival_rate,
            burst_config=ue.burst
        )
        
        while True:
            wait = waiting_timer.next_wait()
            time.sleep(wait)
            if time.time() > self.end_time: # 必須將判定放在 wait 之後，否則超過模擬時間依然會跑最後一次發送封包 
                break

            target_ip = random.choice(self.target_ips)
            if ue.packet_size.distribution == "uniform":
                payload_size = random.randint(ue.packet_size.min, ue.packet_size.max)
            else:
                print(f"[ERROR] Unsupported packet size distribution: {ue.packet_size.distribution}")
                return

            print(f"[{iface}] Sending {self.packet_type} to {target_ip} with size {payload_size} bytes.")
            ret = packet_sender.send_packet(
                target_ip=target_ip,
                payload_size=payload_size,
                target_port=9000  # 可為 None TODO: 應該從config 讀取
            )

            if ret['success'] is True:
                print(f"[{iface}] {self.packet_type} sent successfully: {ret}")
                # 只在成功時才記錄封包
                self.recorder.record_packet(
                    ue.id,
                    iface,
                    payload_size,
                    src_ip=ret['src_ip'],
                    dst_ip=ret['dst_ip'],
                    src_port=ret['src_port'],
                    dst_port=ret['dst_port']
                )
            else:
                print(f"[{iface}] {self.packet_type} failed: {ret}")
                break

    def validate_ue_profiles(self):
        # 首先檢查是否有足夠的權限綁定到網路介面
        if not check_interface_binding_permission():
            print(f"[ERROR] ❌ Insufficient privileges to bind to network interfaces.")
            print(f"[ERROR] ❌ ➡ Please run this program with sudo privileges: sudo python3 ")
            return False
        
        for ue in self.ue_profiles:
            iface = f"uesimtun{ue.id}"
            if not os.path.exists(f"/sys/class/net/{iface}"):
                print(f"[ERROR] Interface '{iface}' does not exist. UE {ue.id} cannot be simulated. --> Exit!!!! ")
                return False
        print("[INFO] All interfaces exist and permissions are sufficient. Proceeding with simulation.")
        return True

    # Monitoring the packet send by each UE
    def start_monitor(self) -> threading.Thread:
        
        monitor_thread = threading.Thread(target=self.display.start_live_bar_chart, daemon=True,
                                          args=())
        monitor_thread.start()
        return monitor_thread
    
    def run(self) -> bool:
        if not self.validate_ue_profiles():
            return False
        
        for ue in self.ue_profiles:
            t = threading.Thread(target=self.simulate_ue, args=(ue,))
            self.threads.append(t)
            t.start()
        
        monitor_thread = self.start_monitor()

        return True

    def wait_for_completion(self):
        for t in self.threads:
            t.join()
        while time.time() < self.end_time:
            time.sleep(1)
        print("[INFO] Simulation completed.")

        # save results to file
        self.recorder.save_csv()

        # plot the scatter plot
        self.display.plot_scatter_and_volume_bar()


if __name__ == "__main__":
    from config_module import BurstRange

    profiles = [
        {
            "name": "high_traffic",
            "arrival_rate": 20,
            "burst": Burst(
                enabled=True,
                burst_chance=0.4,
                burst_arrival_rate=1000,
                burst_on_duration=BurstRange(min=0.5, max=1.5),
                burst_off_duration=BurstRange(min=2, max=10),
            ),
        },
        {
            "name": "mid_traffic",
            "arrival_rate": 10,
            "burst": Burst(
                enabled=True,
                burst_chance=0.2,
                burst_arrival_rate=100,
                burst_on_duration=BurstRange(min=1.0, max=2.0),
                burst_off_duration=BurstRange(min=10.0, max=20.0),
            ),
        },
        {
            "name": "low_traffic",
            "arrival_rate": 1,
            "burst": Burst(enabled=False),
        },
    ]

    print("\n=== Simulated Poisson Wait Times (No real delay) ===\n")
    for profile in profiles:
        print(f"[{profile['name']}] Simulating packet arrivals for 10 seconds...")

        generator = PoissonWaitGenerator(
            arrival_rate=profile["arrival_rate"],
            burst_config=profile["burst"]
        )

        current_time = 0
        wait_times = []
        while current_time < 10:
            wait = generator.next_wait()
            wait_times.append(wait)
            current_time += wait

        print(f"  Simulated packets: {len(wait_times)}")
        print(f"  Total simulated time: {current_time:.2f} sec")
        print(f"  Avg wait: {sum(wait_times)/len(wait_times):.2f} sec")
        print(f"  Min wait: {min(wait_times):.2f} sec")
        print(f"  Max wait: {max(wait_times):.2f} sec")
        print("  First 30 waits:", [f"{w:.2f}" for w in wait_times[:30]])
        print("-" * 60)
    print("\nSimulation completed (no actual waiting).")