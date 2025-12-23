import socket
import os
import logging
from typing import Optional, Dict
from .utils import get_interface_ip, bind_socket_to_interface, calculate_payload_size_from_total_size

logger = logging.getLogger("UE-traffic")


class UDPSender:
    def __init__(self, iface: str):
        self.iface = iface
        if not os.path.exists(f"/sys/class/net/{iface}"):
            raise ValueError(f"Interface {iface} does not exist.")

        # 在初始化時就獲取該 interface 的 IP 地址
        self.interface_ip = get_interface_ip(iface)
        if self.interface_ip is None:
            logger.warning(f"Could not determine IP address for interface '{iface}'")
            self.interface_ip = "unknown"
        else:
            logger.debug(f"Interface '{iface}' IP: {self.interface_ip}")

        # 創建單一 socket 並綁定到介面（不綁定固定源端口，讓系統自動分配）
        # 這樣可以避免為每個目標端口創建 socket，防止文件描述符耗盡
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        bind_socket_to_interface(self.sock, self.iface, strict=True)
        logger.debug(f"Created UDP socket on {self.iface}")

    def send_packet(self, *, target_ip: str, payload_size: int, target_port: Optional[int] = None):
        try:
            # 計算實際 payload 大小（減去 UDP header）
            # payload_size 參數現在表示總封包大小，而不是 payload 大小
            actual_payload_size = calculate_payload_size_from_total_size('udp', payload_size)
            
            # 生成全 0 的 payload（最高效方式）
            payload = bytes(actual_payload_size)
            
            # 使用單一 socket 發送到任意目標端口
            # 源端口由系統自動分配（第一次發送後固定）
            self.sock.sendto(payload, (target_ip, target_port))
            
            # 獲取源端口（第一次發送後會被分配）
            try:
                _, src_port = self.sock.getsockname()
            except:
                src_port = 0  # 如果無法獲取，使用 0
            
            # 返回 5-tuple 信息：(src_ip, src_port, dst_ip, dst_port, protocol)
            return {
                'src_ip': self.interface_ip,
                'src_port': src_port,
                'dst_ip': target_ip,
                'dst_port': target_port,
                'protocol': 'UDP',
                'success': True
            }
            
        except Exception as e:
            logger.error(f"UDP send failed: {e}")
            return {
                'src_ip': self.interface_ip,
                'src_port': 0,
                'dst_ip': target_ip,
                'dst_port': target_port,
                'protocol': 'UDP',
                'success': False,
                'error': str(e)
            }

    def __del__(self):
        """清理：關閉 socket"""
        try:
            if hasattr(self, 'sock'):
                self.sock.close()
        except:
            pass

