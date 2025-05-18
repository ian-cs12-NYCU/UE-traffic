from .ping_sender import PingSender
from .udp_sender import UDPSender
from .base import PacketSender


def get_packet_sender(packet_type: str, iface: str) -> PacketSender:
    if packet_type == "ping":
        return PingSender(iface)
    elif packet_type == "udp":
        return UDPSender(iface)
    else:
        raise ValueError(f"Unsupported packet type: {packet_type}")
