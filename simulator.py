from typing import List, Dict, Optional
import time
import threading
import random
import os
from dataclasses import dataclass
from ping_utils import send_ping
from ue_generator import UEProfile
from display import display_stats

class Simulator:
    def __init__(
        self,
        ue_profiles: List[UEProfile],
        duration: int,
        target_ips: List[str],
        packet_type: str,
        display_interval: Optional[float] = 1.0
    ):
        self.ue_profiles = ue_profiles
        self.duration = duration
        self.target_ips = target_ips
        self.packet_type = packet_type
        self.start_time = time.time()
        self.end_time = self.start_time + duration
        self.display_interval = 1.0

        # 共用資源
        self.ue_counters: Dict[str, int] = {f"uesimtun{ue.id}": 0 for ue in ue_profiles}
        self.ue_latencies: Dict[str, List[float]] = {f"uesimtun{ue.id}": [] for ue in ue_profiles}
        self.lock = threading.Lock()
        self.threads: List[threading.Thread] = []

    def simulate_ue(self, ue: UEProfile):
        iface = f"uesimtun{ue.id}"
        if ue.packet_arrival_rate <= 0:
            print(f'[INFO] UE {ue.id} has a packet arrival rate of 0. Skipping simulation.')
            return
        while time.time() < self.end_time:
            wait = random.expovariate(ue.packet_arrival_rate)
            time.sleep(wait)
            target_ip = random.choice(self.target_ips)

            

            if ue.packet_size.distribution == "uniform":
                payload_size = random.randint(ue.packet_size.min, ue.packet_size.max)
            else:
                print(f"[ERROR] Unsupported packet size distribution: {ue.packet_size.distribution}")
                return

            print(f"[{iface}] Sending {self.packet_type} to {target_ip} with size {payload_size} bytes.")
            if self.packet_type == "ping":
                send_ping(
                    iface=iface,
                    payload_size=payload_size,
                    target_ip=target_ip,
                    counter_dict=self.ue_counters,
                    lock=self.lock,
                    log_latency=True,
                    latency_dict=self.ue_latencies
                )

    def validate_ue_profiles(self):
        for ue in self.ue_profiles:
            iface = f"uesimtun{ue.id}"
            if not os.path.exists(f"/sys/class/net/{iface}"):
                print(f"[ERROR] Interface '{iface}' does not exist. UE {ue.id} cannot be simulated. --> Exit!!!! ")
                return False
        print("[INFO] All interfaces exist. Proceeding with simulation.")
        return True

    # Monitoring the packet send by each UE
    def start_monitor(self) -> threading.Thread:
        monitor_thread = threading.Thread(target=display_stats, daemon=True,
                                          args=(self.ue_counters, self.lock, self.display_interval))
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

        # TODO: Display results
        # TODO: save results to file