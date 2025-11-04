"""
網路工具模組 - 處理 CIDR 網段到 IP 地址列表的轉換
"""

import ipaddress
from typing import List


def expand_subnets_to_ips(subnets: List[str]) -> List[str]:
    """
    將 CIDR 網段列表展開成所有可用的 IP 地址列表
    
    Args:
        subnets: CIDR 網段列表，例如 ["10.201.10.0/24", "192.168.1.0/28"]
        
    Returns:
        展開後的 IP 地址列表，例如 ["10.201.10.1", "10.201.10.2", ..., "192.168.1.1", ...]
        
    Note:
        - 自動排除網路地址（第一個地址）和廣播地址（最後一個地址）
        - /32 網段（單個 IP）會被直接加入列表
        
    Examples:
        >>> expand_subnets_to_ips(["192.168.1.0/30"])
        ['192.168.1.1', '192.168.1.2']
        
        >>> expand_subnets_to_ips(["10.0.0.0/29", "8.8.8.8/32"])
        ['10.0.0.1', '10.0.0.2', '10.0.0.3', '10.0.0.4', '10.0.0.5', '10.0.0.6', '8.8.8.8']
    """
    all_ips = []
    
    for subnet_str in subnets:
        try:
            network = ipaddress.ip_network(subnet_str, strict=False)
            
            # 對於 /32 (單個 IP)，直接加入
            if network.num_addresses == 1:
                all_ips.append(str(network.network_address))
            else:
                # 獲取所有主機地址（自動排除網路地址和廣播地址）
                for ip in network.hosts():
                    all_ips.append(str(ip))
                    
        except ValueError as e:
            print(f"[WARN] Invalid subnet format '{subnet_str}': {e}")
            continue
    
    return all_ips


def get_subnet_info(subnet_str: str) -> dict:
    """
    獲取網段的詳細信息
    
    Args:
        subnet_str: CIDR 網段字符串
        
    Returns:
        包含網段信息的字典：
        {
            'network': str,           # 網路地址
            'netmask': str,           # 子網路遮罩
            'broadcast': str,         # 廣播地址
            'num_addresses': int,     # 總地址數
            'num_usable': int,        # 可用主機數
            'first_ip': str,          # 第一個可用 IP
            'last_ip': str            # 最後一個可用 IP
        }
    """
    try:
        network = ipaddress.ip_network(subnet_str, strict=False)
        
        if network.num_addresses == 1:
            # /32 單個 IP
            return {
                'network': str(network.network_address),
                'netmask': str(network.netmask),
                'broadcast': str(network.network_address),
                'num_addresses': 1,
                'num_usable': 1,
                'first_ip': str(network.network_address),
                'last_ip': str(network.network_address)
            }
        else:
            hosts = list(network.hosts())
            return {
                'network': str(network.network_address),
                'netmask': str(network.netmask),
                'broadcast': str(network.broadcast_address),
                'num_addresses': network.num_addresses,
                'num_usable': len(hosts),
                'first_ip': str(hosts[0]) if hosts else None,
                'last_ip': str(hosts[-1]) if hosts else None
            }
    except ValueError as e:
        return {'error': str(e)}


if __name__ == "__main__":
    """
    測試網路工具功能
    執行方式: python -m lib.network_utils
    """
    print("=" * 70)
    print("網路工具測試 - 網段展開功能")
    print("=" * 70)
    
    # 測試案例
    test_subnets = [
        "10.201.10.0/24",
        "192.168.1.0/28",
        "8.8.8.8/32",
        "172.16.0.0/30"
    ]
    
    print("\n【測試網段】")
    print("-" * 70)
    for subnet in test_subnets:
        print(f"  • {subnet}")
    
    print("\n【網段詳細信息】")
    print("-" * 70)
    
    total_usable = 0
    for subnet in test_subnets:
        info = get_subnet_info(subnet)
        if 'error' not in info:
            print(f"\n  網段: {subnet}")
            print(f"  ├─ 網路地址: {info['network']}")
            print(f"  ├─ 子網遮罩: {info['netmask']}")
            print(f"  ├─ 廣播地址: {info['broadcast']}")
            print(f"  ├─ 總地址數: {info['num_addresses']}")
            print(f"  ├─ 可用主機數: {info['num_usable']}")
            print(f"  └─ IP 範圍: {info['first_ip']} ~ {info['last_ip']}")
            total_usable += info['num_usable']
    
    print("\n" + "-" * 70)
    print(f"  總計: {total_usable} 個可用 IP 地址")
    
    print("\n【IP 列表生成】")
    print("-" * 70)
    
    all_ips = expand_subnets_to_ips(test_subnets)
    print(f"\n  總共生成 {len(all_ips)} 個 IP 地址")
    
    # 顯示每個網段的 IP 數量和示例
    for subnet in test_subnets:
        subnet_ips = expand_subnets_to_ips([subnet])
        print(f"\n  {subnet}: {len(subnet_ips)} 個 IP")
        if len(subnet_ips) <= 10:
            print(f"    → {', '.join(subnet_ips)}")
        else:
            print(f"    → 前 5 個: {', '.join(subnet_ips[:5])}")
            print(f"    → 後 5 個: {', '.join(subnet_ips[-5:])}")
    
    # 流量分布測試
    print("\n【流量分布測試】")
    print("-" * 70)
    
    import random
    from collections import Counter
    
    # 模擬 1000 次隨機選擇
    sample_size = 1000
    selections = [random.choice(all_ips) for _ in range(sample_size)]
    counter = Counter(selections)
    
    print(f"\n  模擬隨機選擇 IP 的分布情況...")
    print(f"  • 模擬次數: {sample_size}")
    print(f"  • 選中的不同 IP 數: {len(counter)}/{len(all_ips)}")
    print(f"  • 理論平均每個 IP 被選中: {sample_size / len(all_ips):.2f} 次")
    
    # 計算分布的統計數據
    import statistics
    counts = list(counter.values())
    mean = statistics.mean(counts)
    stdev = statistics.stdev(counts) if len(counts) > 1 else 0
    
    print(f"\n  分布統計:")
    print(f"  • 實際平均值: {mean:.2f}")
    print(f"  • 標準差: {stdev:.2f}")
    print(f"  • 變異係數: {(stdev/mean)*100:.1f}%")
    
    # 顯示被選中最多和最少的 IP
    most_common = counter.most_common(3)
    least_common = counter.most_common()[-3:]
    
    print(f"\n  被選中最多的 3 個 IP:")
    for ip, count in most_common:
        print(f"    {ip}: {count} 次 ({count/sample_size*100:.1f}%)")
    
    print(f"\n  被選中最少的 3 個 IP:")
    for ip, count in least_common:
        print(f"    {ip}: {count} 次 ({count/sample_size*100:.1f}%)")
    
    print("\n" + "=" * 70)
    print("✓ 測試完成！流量將均勻分布到所有目標 IP 地址")
    print("=" * 70)
    print("\n提示: 使用 'python3 test_subnet_expansion.py' 可測試您的配置文件")

