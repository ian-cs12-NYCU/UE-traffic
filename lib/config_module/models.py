"""
配置數據模型定義
"""

from dataclasses import dataclass
from typing import List, Literal, Optional, Dict

@dataclass
class PacketSize:
    """
    封包大小配置
    
    重要：min 和 max 指定的是「完整數據包大小」(包含所有 header)，而非 payload 大小。
    程序會自動減去 IP 和協議 header，計算實際應該發送的 payload 大小：
    
    - UDP: 最終 payload = 配置大小 - IP_HEADER(20) - UDP_HEADER(8) = 配置大小 - 28
    - TCP: 最終 payload = 配置大小 - IP_HEADER(20) - TCP_HEADER(20) = 配置大小 - 40
    
    例如：
    - 配置 min=54, max=60 (UDP)
      → 網路上看到的數據包大小: 54-60 bytes (包含所有 header)
      → 實際 payload: 54-28=26 ~ 60-28=32 bytes
    """
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
    # 批次發送大小，控制一次發送多少封包後才 sleep
    batch_size: int = 20
    # 日誌等級：DEBUG, INFO, WARNING, ERROR
    log_level: str = "INFO"
    # 是否記錄每個封包的詳細資訊到 CSV（關閉可節省記憶體和 CPU）
    record_packet_details: bool = False

@dataclass
class ParsedConfig:
    simulation: SimulationConfig
    ue_allocation: UEAllocation
    profiles: List[ProfileConfig]
