import socket
import os
import random
import time
from typing import Optional
from .utils import get_interface_ip, bind_socket_to_interface


class TCPSender:
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

    def _create_bound_socket(self) -> socket.socket:
        """創建並綁定到指定介面的 TCP socket"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)  # 3秒超時
        bind_socket_to_interface(sock, self.iface)
        return sock

    def send_packet(self, *, target_ip: str, payload_size: int, target_port: Optional[int] = None):
        """
        發送 TCP 封包並返回 5-tuple 信息
        """
        sock = None
        try:
            # 創建並綁定 TCP socket
            sock = self._create_bound_socket()
            
            # 連接到目標
            sock.connect((target_ip, target_port))
            
            # 獲取連接資訊
            src_ip, src_port = sock.getsockname()
            
            # 生成並發送 payload
            payload = bytes(random.getrandbits(8) for _ in range(payload_size))
            sock.send(payload)
            
            print(f"[{self.iface}] Sent {payload_size} bytes from {src_ip}:{src_port} to {target_ip}:{target_port} via TCP")
            
            # 嘗試接收回應（可選）
            try:
                response = sock.recv(1024)
                print(f"[{self.iface}] Received {len(response)} bytes response")
            except socket.timeout:
                pass  # 沒有回應也沒關係
            
            return {
                'src_ip': src_ip,
                'src_port': src_port,
                'dst_ip': target_ip,
                'dst_port': target_port,
                'protocol': 'TCP',
                'success': True
            }
            
        except Exception as e:
            print(f"[{self.iface}] TCP send failed: {e}")
            return {
                'src_ip': None,
                'src_port': None,
                'dst_ip': target_ip,
                'dst_port': target_port,
                'protocol': 'TCP',
                'success': False,
                'error': str(e)
            }
        finally:
            if sock:
                sock.close()
