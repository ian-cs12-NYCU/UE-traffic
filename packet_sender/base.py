from abc import ABC, abstractmethod
from typing import Optional


class PacketSender(ABC):
    @abstractmethod
    def send_packet(self, *, target_ip: str, payload_size: int, target_port: Optional[int] = None):
        pass
