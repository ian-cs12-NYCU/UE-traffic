from .ping_sender import PingSender
from .udp_sender import UDPSender
from .tcp_sender import TCPSender
from .base import PacketSender


def get_packet_sender(packet_type: str, iface: str) -> PacketSender:
    if packet_type == "ping":
        return PingSender(iface)
    elif packet_type == "udp":
        return UDPSender(iface)
    elif packet_type == "tcp":
        return TCPSender(iface)
    else:
        raise ValueError(f"Unsupported packet type: {packet_type}. Supported types: ping, udp, tcp")
