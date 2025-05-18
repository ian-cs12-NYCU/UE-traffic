from dataclasses import dataclass
from typing import List
from typing import Literal, List
import yaml
from colorama import Fore, Style

@dataclass
class PacketSize:
    distribution: Literal["uniform", "normal"]
    min: int
    max: int


@dataclass
class ProfileConfig:
    name: str
    ue_count: int
    packet_arrival_rate: float
    packet_size: PacketSize


@dataclass
class SimulationConfig:
    record_csv_path: str
    duration_sec: int
    display_interval_sec: int
    packet_type: str
    target_ips: List[str]

@dataclass
class ParsedConfig:
    simulation: SimulationConfig
    profiles: List[ProfileConfig]

def parse_config(path: str = "config/config.yaml") -> ParsedConfig:
    with open(path) as f:
        raw = yaml.safe_load(f)

    sim = raw["simulation"]
    simulation = SimulationConfig(
        record_csv_path=sim["record_csv_path"],
        duration_sec=sim["duration_sec"],
        display_interval_sec=sim["display_interval_sec"],
        packet_type=sim["packet_type"],
        target_ips=sim["target_ips"]
    )

    profiles = []
    for p in raw["ue"]["profiles"]:
        profile = ProfileConfig(
            name=p["name"],
            ue_count=p["ue_count"],
            packet_arrival_rate=p["packet_arrival_rate"],
            packet_size=PacketSize(
                distribution=p["packet_size"]["distribution"],
                min=p["packet_size"]["min"],
                max=p["packet_size"]["max"]
            )
        )
        profiles.append(profile)

    return ParsedConfig(simulation=simulation, profiles=profiles)

if __name__ == "__main__":
    config = parse_config()
    # print the parsed configuration in a readable format
    print("Parsed Configuration:")
    print("Simulation Configuration:")
    print(f"  Duration (sec): {config.simulation.duration_sec}")
    print(f"  Display Interval (sec): {config.simulation.display_interval_sec}")
    print(f"  Packet Type: {config.simulation.packet_type}")
    print(f"  Target IPs: [{'],   ['.join(config.simulation.target_ips)}]")
    
    print("User Profiles:")
    for profile in config.profiles:
        print(f"  Profile Name: {profile.name}") 
        print(Fore.GREEN + f"    UE Count: {profile.ue_count}" + Style.RESET_ALL)
        print(f"    Packet Arrival Rate: {profile.packet_arrival_rate} /s")
        print(f"    Packet Size: {profile.packet_size.min} ~ {profile.packet_size.max} byets")
