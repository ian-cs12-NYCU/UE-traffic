from dataclasses import dataclass
from typing import Literal, List
from enum import Enum
import random
from config_parser import ProfileConfig  #  importing from config_parser.py

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

def generate_ue_profiles(profiles: List[ProfileConfig]) -> List[UEProfile]:
    ue_profiles = []
    ue_id = 0
    for profile in profiles:
       # switch
        if profile.name == "high_traffic":
            traffic_class = TrafficClass.HIGH
        elif profile.name == "low_traffic":
            traffic_class = TrafficClass.LOW
        elif profile.name == "mid_traffic":
            traffic_class = TrafficClass.MID
        else:
            traffic_class = TrafficClass.NONE


        for i in range(profile.ue_count):
            ue_id += 1
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
                packet_size=packet_size
            )
            ue_profiles.append(ue_profile)

    return ue_profiles

if __name__ == "__main__":
    # Example usage
    profiles = [
        ProfileConfig(name="high_traffic", ue_count=3, packet_arrival_rate=2, packet_size=PacketSize(min=64, max=128)),
        ProfileConfig(name="mid_traffic", ue_count=1, packet_arrival_rate=0.3, packet_size=PacketSize(min=256, max=512)),
        ProfileConfig(name="low_traffic", ue_count=3, packet_arrival_rate=0.1, packet_size=PacketSize(min=128, max=256)),
    ]

    ue_profiles = generate_ue_profiles(profiles)
    for profile in ue_profiles:
        print(profile)