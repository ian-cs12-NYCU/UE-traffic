from .ping_sender import PingSender
from .udp_sender import UDPSender
from .tcp_sender import TCPSender
from .base import PacketSender
from typing import Literal, Optional


def get_packet_sender(
    packet_type: str, 
    iface: str, 
    tcp_attack_mode: Optional[Literal["syn", "lazy_mimic_tls"]] = "syn"
) -> PacketSender:
    """
    創建對應的封包發送器
    
    Args:
        packet_type: 封包類型 (ping, udp, tcp)
        iface: 網路介面名稱
        tcp_attack_mode: TCP 攻擊模式（僅當 packet_type="tcp" 時有效）
            - "syn": 傳統 TCP SYN flood
            - "lazy_mimic_tls": 偽造 TLS 握手攻擊
    
    Returns:
        對應的封包發送器實例
    """
    if packet_type == "ping":
        return PingSender(iface)
    elif packet_type == "udp":
        return UDPSender(iface)
    elif packet_type == "tcp":
        return TCPSender(iface, tcp_attack_mode=tcp_attack_mode)
    else:
        raise ValueError(f"Unsupported packet type: {packet_type}. Supported types: ping, udp, tcp")
