import socket
import os
import random
from typing import Optional


class UDPSender:
    def __init__(self, iface: str):
        self.iface = iface
        if not os.path.exists(f"/sys/class/net/{iface}"):
            raise ValueError(f"Interface {iface} does not exist.")

        # 建立 UDP socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # 可選：綁定 interface（這行需要 root，否則請註解掉）
        try:
            self.sock.setsockopt(socket.SOL_SOCKET, 25, iface.encode())  # 25 = SO_BINDTODEVICE
        except PermissionError:
            print(f"[WARN] Cannot bind to interface '{iface}' (need root), using default route")

    def send_packet (self, *, target_ip: str, payload_size: int, target_port: Optional[int] = None):
        try:
            payload = bytes(random.getrandbits(8) for _ in range(payload_size))
            self.sock.sendto(payload, (target_ip, target_port))
            print(f"[{self.iface}] Sent {payload_size} bytes to {target_ip}:{target_port}")
        except Exception as e:
            print(f"[{self.iface}] UDP send failed: {e}")

