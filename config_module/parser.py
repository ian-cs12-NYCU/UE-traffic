"""
配置文件解析器
"""

import yaml
from .models import (
    PacketSize, BurstRange, Burst, UEAllocation, 
    ProfileConfig, SimulationConfig, ParsedConfig
)

def parse_config(path: str = "config/config.yaml") -> ParsedConfig:
    """
    解析配置文件
    
    Args:
        path: 配置文件路徑
        
    Returns:
        ParsedConfig: 解析後的配置對象
        
    Raises:
        ValueError: 當配置驗證失敗時
        FileNotFoundError: 當配置文件不存在時
        yaml.YAMLError: 當YAML格式錯誤時
    """
    try:
        with open(path, 'r', encoding='utf-8') as f:
            raw = yaml.safe_load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"配置文件 {path} 不存在")
    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"配置文件 {path} 格式錯誤: {e}")

    # 解析 simulation 配置
    sim = raw["simulation"]
    simulation = SimulationConfig(
        record_csv_path=sim["record_csv_path"],
        duration_sec=sim["duration_sec"],
        display_interval_sec=sim["display_interval_sec"],
        packet_type=sim["packet_type"],
        target_ips=sim["target_ips"]
    )

    # 解析 UE allocation 配置
    ue_config = raw["ue"]
    allocation = ue_config["allocation"]
    ue_allocation = UEAllocation(
        total_count=allocation["total_count"],
        distribution=allocation["distribution"]
    )

    # 驗證分配總數
    distributed_total = sum(ue_allocation.distribution.values())
    if distributed_total != ue_allocation.total_count:
        raise ValueError(
            f"分配總數 ({distributed_total}) 與 total_count ({ue_allocation.total_count}) 不匹配"
        )

    # 解析 profiles 配置
    profiles = []
    for p in ue_config["profiles"]:
        burst_config = p.get("burst", {})
        if burst_config.get("enable", False):
            burst = Burst(
                enabled=True,
                burst_chance=burst_config["burst_chance"],
                burst_arrival_rate=burst_config["burst_arrival_rate"],
                burst_on_duration=BurstRange(
                    min=burst_config["burst_on_duration"]["min"],
                    max=burst_config["burst_on_duration"]["max"]
                ),
                burst_off_duration=BurstRange(
                    min=burst_config["burst_off_duration"]["min"],
                    max=burst_config["burst_off_duration"]["max"]
                )
            )
        else:
            burst = Burst(enabled=False)

        profile = ProfileConfig(
            name=p["name"],
            packet_arrival_rate=p["packet_arrival_rate"],
            packet_size=PacketSize(
                distribution=p["packet_size"]["distribution"],
                min=p["packet_size"]["min"],
                max=p["packet_size"]["max"]
            ),
            burst=burst
        )

        profiles.append(profile)

    # 驗證 profiles 中的名稱是否與 allocation 中的一致
    profile_names = {p.name for p in profiles}
    allocation_names = set(ue_allocation.distribution.keys())
    
    if profile_names != allocation_names:
        missing_in_profiles = allocation_names - profile_names
        missing_in_allocation = profile_names - allocation_names
        
        error_msg = []
        if missing_in_profiles:
            error_msg.append(f"Allocation 中定義但 profiles 中缺少: {missing_in_profiles}")
        if missing_in_allocation:
            error_msg.append(f"Profiles 中定義但 allocation 中缺少: {missing_in_allocation}")
        
        raise ValueError("; ".join(error_msg))

    return ParsedConfig(simulation=simulation, ue_allocation=ue_allocation, profiles=profiles)
