"""
端口工具模組 - 處理端口配置字串到端口列表的轉換
"""

from typing import List
import logging

logger = logging.getLogger("UE-traffic")


def parse_port_string(port_string: str) -> List[int]:
    """
    解析端口配置字串，支援單個端口、多個端口和端口範圍
    
    Args:
        port_string: 端口配置字串，例如：
            - "80" - 單個端口
            - "80, 443, 8080" - 多個端口
            - "8000-8010" - 端口範圍
            - "80, 443, 8000-8010" - 混合使用
            
    Returns:
        展開後的端口列表，例如 [80, 443, 8000, 8001, ..., 8010]
        
    Examples:
        >>> parse_port_string("80")
        [80]
        
        >>> parse_port_string("80, 443, 8080")
        [80, 443, 8080]
        
        >>> parse_port_string("8000-8003")
        [8000, 8001, 8002, 8003]
        
        >>> parse_port_string("80, 443, 8000-8003")
        [80, 443, 8000, 8001, 8002, 8003]
    """
    ports = []
    
    # 移除空白字符並分割
    parts = [part.strip() for part in port_string.split(',')]
    
    for part in parts:
        if not part:
            continue
            
        # 檢查是否為範圍（包含 '-'）
        if '-' in part:
            try:
                start, end = part.split('-', 1)
                start_port = int(start.strip())
                end_port = int(end.strip())
                
                # 驗證端口範圍
                if not (1 <= start_port <= 65535 and 1 <= end_port <= 65535):
                    logger.warning(f"Invalid port range '{part}': ports must be between 1-65535")
                    continue
                    
                if start_port > end_port:
                    logger.warning(f"Invalid port range '{part}': start port > end port")
                    continue
                
                # 展開範圍
                ports.extend(range(start_port, end_port + 1))
                
            except ValueError as e:
                logger.warning(f"Invalid port range format '{part}': {e}")
                continue
        else:
            # 單個端口
            try:
                port = int(part.strip())
                
                # 驗證端口號
                if not (1 <= port <= 65535):
                    logger.warning(f"Invalid port '{port}': must be between 1-65535")
                    continue
                    
                ports.append(port)
                
            except ValueError as e:
                logger.warning(f"Invalid port format '{part}': {e}")
                continue
    
    # 移除重複並排序
    ports = sorted(set(ports))
    
    return ports


def get_port_config_info(port_string: str) -> dict:
    """
    獲取端口配置的詳細信息
    
    Args:
        port_string: 端口配置字串
        
    Returns:
        包含端口信息的字典：
        {
            'original': str,          # 原始配置字串
            'parsed_ports': List[int], # 解析後的端口列表
            'num_ports': int,          # 端口總數
            'min_port': int,           # 最小端口號
            'max_port': int            # 最大端口號
        }
    """
    ports = parse_port_string(port_string)
    
    if not ports:
        return {
            'original': port_string,
            'parsed_ports': [],
            'num_ports': 0,
            'min_port': None,
            'max_port': None,
            'error': 'No valid ports found'
        }
    
    return {
        'original': port_string,
        'parsed_ports': ports,
        'num_ports': len(ports),
        'min_port': min(ports),
        'max_port': max(ports)
    }


if __name__ == "__main__":
    """
    測試端口解析功能
    執行方式: python -m lib.port_utils
    """
    print("=" * 70)
    print("端口工具測試 - 端口配置解析功能")
    print("=" * 70)
    
    # 測試案例
    test_cases = [
        "80",
        "80, 443, 8080",
        "8000-8005",
        "80, 443, 8000-8003",
        "53, 80, 443, 3000-3005, 8080, 9000-9002",
        "10-15, 20, 30-32",
    ]
    
    print("\n【測試案例】")
    print("-" * 70)
    
    for test_string in test_cases:
        print(f"\n配置字串: \"{test_string}\"")
        
        info = get_port_config_info(test_string)
        
        if 'error' in info:
            print(f"  ✗ 錯誤: {info['error']}")
            continue
        
        print(f"  ✓ 解析成功")
        print(f"  • 端口總數: {info['num_ports']}")
        print(f"  • 端口範圍: {info['min_port']} ~ {info['max_port']}")
        
        if info['num_ports'] <= 20:
            print(f"  • 完整列表: {info['parsed_ports']}")
        else:
            print(f"  • 前 10 個: {info['parsed_ports'][:10]}")
            print(f"  • 後 10 個: {info['parsed_ports'][-10:]}")
    
    # 流量分布測試
    print("\n【流量分布測試】")
    print("-" * 70)
    
    test_config = "80, 443, 8000-8010"
    print(f"\n測試配置: \"{test_config}\"")
    
    ports = parse_port_string(test_config)
    print(f"  生成端口列表: {ports}")
    
    import random
    from collections import Counter
    
    # 模擬 1000 次隨機選擇
    sample_size = 1000
    selections = [random.choice(ports) for _ in range(sample_size)]
    counter = Counter(selections)
    
    print(f"\n  模擬隨機選擇端口的分布情況...")
    print(f"  • 模擬次數: {sample_size}")
    print(f"  • 端口總數: {len(ports)}")
    print(f"  • 理論平均每個端口被選中: {sample_size / len(ports):.2f} 次")
    
    # 計算分布的統計數據
    import statistics
    counts = list(counter.values())
    mean = statistics.mean(counts)
    stdev = statistics.stdev(counts) if len(counts) > 1 else 0
    
    print(f"\n  分布統計:")
    print(f"  • 實際平均值: {mean:.2f}")
    print(f"  • 標準差: {stdev:.2f}")
    print(f"  • 變異係數: {(stdev/mean)*100:.1f}%")
    
    # 顯示被選中最多和最少的端口
    most_common = counter.most_common(3)
    least_common = counter.most_common()[-3:]
    
    print(f"\n  被選中最多的 3 個端口:")
    for port, count in most_common:
        print(f"    {port}: {count} 次 ({count/sample_size*100:.1f}%)")
    
    print(f"\n  被選中最少的 3 個端口:")
    for port, count in least_common:
        print(f"    {port}: {count} 次 ({count/sample_size*100:.1f}%)")
    
    print("\n" + "=" * 70)
    print("✓ 測試完成！流量將均勻分布到所有指定的端口")
    print("=" * 70)
