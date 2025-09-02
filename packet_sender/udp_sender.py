import socket
import os
import random
from typing import Optional
from .utils import get_interface_ip, bind_socket_to_interface


class UDPSender:
    def __init__(self, iface: str):
        self.iface = iface
        if not os.path.exists(f"/sys/class/net/{iface}"):
            raise ValueError(f"Interface {iface} does not exist.")

        # 在初始化時就獲取該 interface 的 IP 地址
        self.interface_ip = get_interface_ip(iface)
        if self.interface_ip is None:
            print(f"[WARN] Could not determine IP address for interface '{iface}'")
            self.interface_ip = "unknown"
        else:
            print(f"[INFO] Interface '{iface}' IP: {self.interface_ip}")

        # 初始化時創建並綁定 UDP socket
        self._setup_socket()

    def _setup_socket(self):
        """創建並綁定到指定介面的 UDP socket"""
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # 使用嚴格模式，如果綁定失敗會拋出異常
        bind_socket_to_interface(self.sock, self.iface, strict=True)

    def send_packet(self, *, target_ip: str, payload_size: int, target_port: Optional[int] = None):
        try:
            # 生成隨機 payload
            payload = bytes(random.getrandbits(8) for _ in range(payload_size))
            
            # 如果 socket 還沒有綁定端口，讓系統自動分配
            if self.sock.getsockname()[1] == 0:
                self.sock.bind(('', 0))  # 綁定到隨機可用端口
            
            # 發送 UDP 封包
            self.sock.sendto(payload, (target_ip, target_port))
            
            # 獲取實際的源端口
            _, src_port = self.sock.getsockname()
            
            # 使用初始化時獲取的 interface IP
            src_ip = self.interface_ip
            
            print(f"[{self.iface}] Sent {payload_size} bytes from {src_ip}:{src_port} to {target_ip}:{target_port}")
            
            # 返回 5-tuple 信息：(src_ip, src_port, dst_ip, dst_port, protocol)
            return {
                'src_ip': src_ip,
                'src_port': src_port,
                'dst_ip': target_ip,
                'dst_port': target_port,
                'protocol': 'UDP',
                'success': True
            }
            
        except Exception as e:
            print(f"[{self.iface}] UDP send failed: {e}")
            return {
                'src_ip': self.interface_ip,  # 即使失敗也使用已知的 interface IP
                'src_port': None,
                'dst_ip': target_ip,
                'dst_port': target_port,
                'protocol': 'UDP',
                'success': False,
                'error': str(e)
            }

