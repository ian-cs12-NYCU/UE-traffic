"""
配置顯示工具
"""

from colorama import Fore, Style
from .models import ParsedConfig

def display_config(config: ParsedConfig) -> None:
    """
    以易讀格式顯示配置信息
    
    Args:
        config: 解析後的配置對象
    """
    print("Parsed Configuration:")
    print("=" * 50)
    
    # 顯示 Simulation 配置
    print("Simulation Configuration:")
    print(f"  Duration (sec): {config.simulation.duration_sec}")
    print(f"  Display Interval (sec): {config.simulation.display_interval_sec}")
    print(f"  Packet Type: {config.simulation.packet_type}")
    print(f"  Record Path: {config.simulation.record_csv_path}")
    print(f"  Target IPs: [{'], ['.join(config.simulation.target_ips)}]")
    
    # 顯示 UE Allocation
    print("\nUE Allocation:")
    print(Fore.GREEN + f"  Total UE Count: {config.ue_allocation.total_count}" + Style.RESET_ALL)
    print("  Distribution:")
    for profile_name, count in config.ue_allocation.distribution.items():
        percentage = (count / config.ue_allocation.total_count) * 100
        print(f"    {profile_name}: {count} ({percentage:.1f}%)")
    
    # 顯示 Profiles
    print("\nUser Profiles:")
    for i, profile in enumerate(config.profiles, 1):
        ue_count = config.ue_allocation.distribution.get(profile.name, 0)
        print(f"  [{i}] Profile: {profile.name} ({ue_count} UEs)")
        print(f"      Packet Arrival Rate: {profile.packet_arrival_rate} packets/s")
        print(f"      Packet Size: {profile.packet_size.min}~{profile.packet_size.max} bytes ({profile.packet_size.distribution})")
        print(f"      Burst Enabled: {profile.burst.enabled}")
        
        if profile.burst.enabled:
            print(f"      Burst Settings:")
            print(f"        - Chance: {profile.burst.burst_chance}")
            print(f"        - Arrival Rate: {profile.burst.burst_arrival_rate} packets/s")
            print(f"        - On Duration: {profile.burst.burst_on_duration.min}~{profile.burst.burst_on_duration.max} sec")
            print(f"        - Off Duration: {profile.burst.burst_off_duration.min}~{profile.burst.burst_off_duration.max} sec")
        
        if i < len(config.profiles):
            print()
    
    print(Style.RESET_ALL)
    print("Configuration parsing completed successfully.")

def display_summary(config: ParsedConfig) -> None:
    """
    顯示配置摘要信息
    
    Args:
        config: 解析後的配置對象
    """
    print(f"總UE數: {config.ue_allocation.total_count}")
    print(f"測試時長: {config.simulation.duration_sec}秒")
    print(f"封包類型: {config.simulation.packet_type.upper()}")
    print(f"Profile數量: {len(config.profiles)}")
    
    print("\n分配詳情:")
    for name, count in config.ue_allocation.distribution.items():
        percentage = (count / config.ue_allocation.total_count) * 100
        print(f"  {name}: {count} ({percentage:.1f}%)")
