from typing import List, Dict, Optional
import time
import threading
import random
import os
from dataclasses import dataclass

from ..config_module import ParsedConfig, Burst
from ..packet_sender import get_packet_sender
from ..packet_sender.utils import check_interface_binding_permission, format_interface_name
from ..ue_generator import UEProfile
from ..display import Display
from ..recorder import Recorder
from ..network_utils import expand_subnets_to_ips
from ..port_utils import parse_port_string

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
        
        # 從 CIDR 網段展開成 IP 地址列表
        print(f"[INFO] Expanding subnets: {cfg.simulation.target_subnets}")
        self.target_ips = expand_subnets_to_ips(cfg.simulation.target_subnets)
        
        if not self.target_ips:
            raise ValueError("No valid IP addresses generated from target_subnets. Please check your configuration.")
        
        print(f"[INFO] Generated {len(self.target_ips)} target IP addresses")
        if len(self.target_ips) <= 10:
            print(f"[INFO] Target IPs: {', '.join(self.target_ips)}")
        else:
            print(f"[INFO] First 5 IPs: {', '.join(self.target_ips[:5])}")
            print(f"[INFO] Last 5 IPs: {', '.join(self.target_ips[-5:])}")
        
        # 解析目標端口配置
        print(f"[INFO] Parsing target ports: {cfg.simulation.target_ports}")
        self.target_ports = parse_port_string(cfg.simulation.target_ports)
        
        if not self.target_ports:
            raise ValueError("No valid ports generated from target_ports. Please check your configuration.")
        
        print(f"[INFO] Generated {len(self.target_ports)} target ports")
        if len(self.target_ports) <= 20:
            print(f"[INFO] Target Ports: {self.target_ports}")
        else:
            print(f"[INFO] First 10 ports: {self.target_ports[:10]}")
            print(f"[INFO] Last 10 ports: {self.target_ports[-10:]}")
        
        self.packet_type = cfg.simulation.packet_type
        # keep full config for building interface names
        self.cfg = cfg
        self.start_time = time.time()
        self.end_time = self.start_time + self.duration
        self.recorder = Recorder(self.lock, self.ue_profiles, cfg.simulation.record_csv_path)
        self.display = Display(self.recorder, self.lock, cfg.simulation.display_interval_sec)
 
    def simulate_ue(self, ue: UEProfile):
        """
        模擬單一 UE 的封包發送行為（使用批次發送提高精度）
        
        批次發送原理：
        1. 使用 Poisson process 生成封包間隔時間（維持理論流量分佈）
        2. 累積 batch_size 個封包的間隔時間
        3. 快速連續發送這一批封包
        4. Sleep 累積的總時間減去實際發送耗時
        
        優點：
        - time.sleep() 使用較長的時間（如 10ms），作業系統能更精確控制
        - 實際達成的 bitrate 更接近理論值
        - 不影響 Poisson 分佈特性（間隔時間仍由 Poisson process 產生）
        
        範例：
        - packet_arrival_rate = 2000 pps, batch_size = 20
        - 每批次間隔 = 20/2000 = 0.01 秒 (10ms)
        - 10ms 比 0.5ms 更容易精確控制
        """
        # 根據 simulator type 建立介面名稱
        iface = format_interface_name(self.cfg.simulation.ue_simulator_type, ue.id)
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
        
        # 批次發送相關變數
        batch_size = self.cfg.simulation.batch_size
        packets_to_send = []  # 待發送封包的佇列
        
        while True:
            # 使用 Poisson process 產生下一個封包的等待時間
            wait = waiting_timer.next_wait()
            
            # 累積封包到批次中（不實際 sleep）
            if time.time() + wait > self.end_time:
                # 如果下一個封包會超過模擬時間，發送剩餘的封包後結束
                break
            
            packets_to_send.append(wait)
            
            # 當累積到足夠的封包數量時，進行批次發送
            if len(packets_to_send) >= batch_size:
                # 計算批次間隔時間（理論上這批封包應該跨越的總時間）
                batch_total_wait = sum(packets_to_send)
                
                batch_start = time.time()
                
                # 批次發送所有封包
                for _ in range(len(packets_to_send)):
                    if time.time() > self.end_time:
                        break
                    
                    target_ip = random.choice(self.target_ips)
                    target_port = random.choice(self.target_ports)
                    
                    if ue.packet_size.distribution == "uniform":
                        payload_size = random.randint(ue.packet_size.min, ue.packet_size.max)
                    else:
                        print(f"[ERROR] Unsupported packet size distribution: {ue.packet_size.distribution}")
                        return

                    print(f"[{iface}] Sending {self.packet_type} to {target_ip}:{target_port} with size {payload_size} bytes.")
                    ret = packet_sender.send_packet(
                        target_ip=target_ip,
                        payload_size=payload_size,
                        target_port=target_port
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
                
                # 計算實際發送耗時
                elapsed = time.time() - batch_start
                
                # 扣除發送耗時後，sleep 剩餘時間以維持正確的發送速率
                sleep_time = batch_total_wait - elapsed
                if sleep_time > 0:
                    time.sleep(sleep_time)
                
                # 清空佇列，準備下一批
                packets_to_send = []

    def validate_ue_profiles(self):
        # 首先檢查是否有足夠的權限綁定到網路介面
        if not check_interface_binding_permission():
            print(f"[ERROR] ❌ Insufficient privileges to bind to network interfaces.")
            print(f"[ERROR] ❌ ➡ Please run this program with sudo privileges: sudo python3 ")
            return False
        
        # 根據 simulator type 建立並驗證介面名稱
        # 不存在的介面會被標記，但不會直接退出
        valid_ues = []
        skipped_ues = []
        
        for ue in self.ue_profiles:
            iface = format_interface_name(self.cfg.simulation.ue_simulator_type, ue.id)
            if not os.path.exists(f"/sys/class/net/{iface}"):
                print(f"[WARN] ⚠ Interface '{iface}' does not exist. UE {ue.id} will be skipped.")
                skipped_ues.append(ue)
            else:
                valid_ues.append(ue)
        
        # 更新 ue_profiles 只保留有效的 UE
        self.ue_profiles = valid_ues
        
        if len(self.ue_profiles) == 0:
            print(f"[ERROR] ❌ No valid interfaces found. Cannot proceed with simulation.")
            return False
        
        print(f"[INFO] ✓ Found {len(valid_ues)} valid interface(s), {len(skipped_ues)} skipped.")
        print("[INFO] All permissions are sufficient. Proceeding with simulation.")
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
    from ..config_module import BurstRange

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