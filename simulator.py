from typing import List, Dict, Optional
import time
import threading
import random
import os
from dataclasses import dataclass

from config_parser import ParsedConfig
from ping_utils import PingSender
from ue_generator import UEProfile
from display import Display
from recorder import Recorder



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

        ping_sender = PingSender(
            iface=iface,
        )
        while time.time() < self.end_time:
            wait = random.expovariate(ue.packet_arrival_rate)
            print(f"[{iface}] Waiting for {wait:.2f} seconds (arrival rate: {ue.packet_arrival_rate:.2f})")
            time.sleep(wait)
            target_ip = random.choice(self.target_ips)

            if ue.packet_size.distribution == "uniform":
                payload_size = random.randint(ue.packet_size.min, ue.packet_size.max)
            else:
                print(f"[ERROR] Unsupported packet size distribution: {ue.packet_size.distribution}")
                return

            print(f"[{iface}] Sending {self.packet_type} to {target_ip} with size {payload_size} bytes.")
            if self.packet_type == "ping":
                ping_sender.send_ping(payload_size=payload_size, target_ip=target_ip)
                self.recorder.record_packet(
                    ue.id,
                    iface,
                    payload_size,
                    # ping_sender.get_ping_latency(target_ip),
                )
                self.recorder.increment_ue_packet_cnt(ue.id)

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

        # TODO: save results to file
        self.recorder.save_csv()

        # TODO:plot the scatter plot
        self.display.plot_scatter_and_volume_bar()
