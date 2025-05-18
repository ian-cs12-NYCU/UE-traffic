import subprocess
import os
from datetime import datetime


class PingSender:
    def __init__(self, iface: str):
        self.iface = iface

    def send_ping(self, payload_size: int = 0, target_ip: str = None):
        if not os.path.exists(f"/sys/class/net/{self.iface}"):
            print(f"[ERROR] Network interface '{self.iface}' does not exist.")
            return

        try:
            result = subprocess.run(
                ["ping", "-I", self.iface, "-c", "1", "-W", "1", target_ip, "-s", str(payload_size)],
                capture_output=True,
                text=True
            )
            now = datetime.now().timestamp()
            
            if result.returncode != 0: # Failed ping
                print(f"[{self.iface}] No reply from {target_ip} !!!")
                return
            
            # TODO: acquire latency
            # example ping output: "64 bytes from 8.8.8.8: icmp_seq=1 ttl=116 time=4.33 ms

        except Exception as e:
            print(f"[{self.iface}] Ping failed: {e}")
            return

    
