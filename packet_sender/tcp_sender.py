import socket
import os
import random
import time
import subprocess
from typing import Optional


def get_interface_ip(iface: str) -> Optional[str]:
    """獲取指定介面的 IP 地址"""
    try:
        result = subprocess.run(['ip', 'addr', 'show', iface], 
                              capture_output=True, text=True, check=True)
        lines = result.stdout.split('\n')
        for line in lines:
            if 'inet ' in line and not line.strip().startswith('inet 127.'):
                ip_part = line.strip().split('inet ')[1].split(' ')[0]
                ip = ip_part.split('/')[0]
                return ip
    except:
        pass
    return None


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

    def send_packet(self, *, target_ip: str, payload_size: int, target_port: Optional[int] = None):
        """
        發送 TCP 封包並返回 5-tuple 信息
        """
        sock = None
        try:
            # 創建 TCP socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)  # 5秒超時
            
            # 可選：綁定 interface（需要 root 權限）
            try:
                sock.setsockopt(socket.SOL_SOCKET, 25, self.iface.encode())  # SO_BINDTODEVICE
            except (PermissionError, OSError):
                pass  # 沒有權限或系統不支援，使用預設路由
            
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
