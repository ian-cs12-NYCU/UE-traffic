from ping3 import ping
import os
from typing import Optional


class PingSender:
    def __init__(self, iface: str):
        self.iface = iface
        if not os.path.exists(f"/sys/class/net/{iface}"):
            raise ValueError(f"Interface {iface} does not exist.")

    def send_packet(self, *, target_ip: str, payload_size: int, target_port: Optional[int] = None):
        try:
            rtt = ping(
                target_ip,
                timeout=1,
                size=payload_size,
                # interface=self.iface,
                unit="ms"
            )
            
            if rtt is None:
                print(f"[{self.iface}] Ping failed: No response from {target_ip}")
                return
            print(f"[{self.iface}] Ping to {target_ip} successful: RTT = {rtt:.2f} ms")
        except Exception as e:
            print(f"[{self.iface}] Ping failed: {e}")
            return

    
