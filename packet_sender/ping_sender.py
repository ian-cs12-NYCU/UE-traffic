from ping3 import ping
import os
import socket
from typing import Optional
from .utils import get_interface_ip, check_interface_binding_permission


class PingSender:
    def __init__(self, iface: str):
        self.iface = iface
        if not os.path.exists(f"/sys/class/net/{iface}"):
            raise ValueError(f"Interface {iface} does not exist.")
        
        # 檢查是否有權限綁定到介面
        if not check_interface_binding_permission():
            raise PermissionError(f"Insufficient privileges to bind to interface '{iface}'. Please run with sudo.")
        
        # 在初始化時就獲取該 interface 的 IP 地址
        self.interface_ip = get_interface_ip(iface)
        if self.interface_ip is None:
            print(f"[WARN] Could not determine IP address for interface '{iface}'")
            self.interface_ip = "unknown"
        else:
            print(f"[INFO] Interface '{iface}' IP: {self.interface_ip}")

    def send_packet(self, *, target_ip: str, payload_size: int, target_port: Optional[int] = None):
        try:
            rtt = ping(
                target_ip,
                timeout=1,
                size=payload_size,
                interface=self.iface,  # 有些系統不支援此參數
                unit="ms"
            )
            
            if rtt is None:
                print(f"[{self.iface}] Ping failed: No response from {target_ip}")
                return {
                    'src_ip': self.interface_ip,  # 使用預先獲取的 IP
                    'src_port': 0,  # ICMP 沒有端口概念
                    'dst_ip': target_ip,
                    'dst_port': 0,
                    'protocol': 'ICMP',
                    'success': False,
                    'latency_ms': None
                }
            
            # 使用初始化時獲取的 interface IP
            src_ip = self.interface_ip
            
            print(f"[{self.iface}] Ping from {src_ip} to {target_ip} successful: RTT = {rtt:.2f} ms")
            
            # 返回 5-tuple + latency 信息
            return {
                'src_ip': src_ip,
                'src_port': 0,  # ICMP 沒有端口概念
                'dst_ip': target_ip,
                'dst_port': 0,
                'protocol': 'ICMP',
                'success': True,
                'latency_ms': rtt
            }
            
        except Exception as e:
            print(f"[{self.iface}] Ping failed: {e}")
            return {
                'error message': str(e),
                'src_ip': self.interface_ip,  # 使用預先獲取的 IP
                'src_port': 0,
                'dst_ip': target_ip,
                'dst_port': 0,
                'protocol': 'ICMP',
                'success': False,
                'latency_ms': None
            }

    
