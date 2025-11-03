from dataclasses import dataclass
from typing import Literal, List, Dict
from enum import Enum
import random
from ..config_module import ProfileConfig, Burst, ParsedConfig  # 更新導入路徑

class TrafficClass(Enum):
    HIGH = "high"
    MID = "mid"
    LOW = "low"
    NONE = "none"

@dataclass
class PacketSize:
    distribution: Literal["uniform", "normal"]
    min: int
    max: int

@dataclass
class UEProfile:
    id: int
    profile_name: str
    traffic_class: TrafficClass
    packet_arrival_rate: float
    packet_size: PacketSize
    burst: Burst

def generate_ue_profiles(config: ParsedConfig) -> List[UEProfile]:
    """Generate UE profiles based on allocation and profile configurations"""
    ue_profiles = []
    # 使用 interface_id_start 作為起始 id
    ue_id = config.simulation.interface_id_start
    
    # Create a mapping from profile names to profile configs
    profile_map = {profile.name: profile for profile in config.profiles}
    
    # Generate UEs according to allocation
    for profile_name, ue_count in config.ue_allocation.distribution.items():
        if profile_name not in profile_map:
            raise ValueError(f"Profile '{profile_name}' in allocation not found in profiles")
        
        profile = profile_map[profile_name]
        
        # Determine traffic class
        if profile.name == "high_traffic":
            traffic_class = TrafficClass.HIGH
        elif profile.name == "low_traffic":
            traffic_class = TrafficClass.LOW
        elif profile.name == "mid_traffic":
            traffic_class = TrafficClass.MID
        else:
            traffic_class = TrafficClass.NONE

        # Generate specified number of UEs for this profile
        for i in range(ue_count):
            packet_size = PacketSize(
                min=profile.packet_size.min,
                max=profile.packet_size.max,
                distribution=profile.packet_size.distribution
            )
            ue_profile = UEProfile(
                id=ue_id,
                profile_name=profile.name,
                traffic_class=traffic_class,
                packet_arrival_rate=profile.packet_arrival_rate,
                packet_size=packet_size,
                burst=profile.burst
            )
            ue_profiles.append(ue_profile)
            ue_id += 1

    return ue_profiles

if __name__ == "__main__":
    from ..config_module import parse_config
    
    # Example usage with new config structure
    config = parse_config("config/config.yaml")
    
    print("Configuration loaded:")
    print(f"Total UEs: {config.ue_allocation.total_count}")
    print("Distribution:")
    for name, count in config.ue_allocation.distribution.items():
        print(f"  {name}: {count}")
    
    ue_profiles = generate_ue_profiles(config)
    
    print(f"\nGenerated {len(ue_profiles)} UE profiles:")
    for profile in ue_profiles:
        print(f"UE {profile.id}: {profile.profile_name} ({profile.traffic_class.value})")
