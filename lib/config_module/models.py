"""
配置數據模型定義
"""

from dataclasses import dataclass
from typing import List, Literal, Optional, Dict

@dataclass
class PacketSize:
    distribution: Literal["uniform", "normal"]
    min: int
    max: int

@dataclass
class BurstRange:
    min: float
    max: float

@dataclass
class Burst:
    enabled: bool
    burst_chance: Optional[float] = None
    burst_arrival_rate: Optional[float] = None
    burst_on_duration: Optional[BurstRange] = None
    burst_off_duration: Optional[BurstRange] = None

@dataclass
class UEAllocation:
    total_count: int
    distribution: Dict[str, int]

@dataclass
class ProfileConfig:
    name: str
    packet_arrival_rate: float
    packet_size: PacketSize
    burst: Burst

@dataclass
class SimulationConfig:
    record_csv_path: str
    duration_sec: int
    display_interval_sec: int
    packet_type: str
    target_subnets: List[str]  # CIDR 網段列表，例如 ["10.201.10.0/24", "192.168.1.0/24"]
    target_ports: str  # 端口配置字串，例如 "80, 443, 8000-8010"
    # UE simulator type determines interface naming: 'ueransim', 'packetrusher', or 'free-ran-ue'
    ue_simulator_type: Literal["ueransim", "packetrusher", "free-ran-ue"] = "packetrusher"
    # Interface ID 起始編號（第一個 UE 使用的 interface id）
    interface_id_start: int = 4

@dataclass
class ParsedConfig:
    simulation: SimulationConfig
    ue_allocation: UEAllocation
    profiles: List[ProfileConfig]
