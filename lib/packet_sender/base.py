from abc import ABC, abstractmethod
from typing import Optional, Dict, Any


class PacketSender(ABC):
    @abstractmethod
    def send_packet(self, *, target_ip: str, payload_size: int, target_port: Optional[int] = None) -> Dict[str, Any]:
        """
        發送封包並返回詳細信息
        
        返回格式：
        {
            'src_ip': str,           # 源 IP 地址
            'src_port': int,         # 源端口（ICMP 為 0）
            'dst_ip': str,           # 目標 IP 地址
            'dst_port': int,         # 目標端口（ICMP 為 0）
            'protocol': str,         # 協議類型 (UDP/TCP/ICMP)
            'success': bool,         # 是否發送成功
            'latency_ms': float,     # 延遲（僅 ICMP ping，可選）
            'error': str             # 錯誤信息（發送失敗時）
        }
        """
        pass
