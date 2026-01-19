#!/usr/bin/env python3
"""
Lazy Mimic TLS 功能測試

測試項目：
1. Payload 結構驗證（Magic Header, Length Field, Random Body）
2. 配置解析
3. TCPSender 初始化
"""

import sys
import os
import struct
import random

# 添加專案路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def generate_lazy_mimic_tls_payload(data_length: int) -> bytes:
    """生成偽造 TLS Payload"""
    magic_header = b'\x16\x03\x01'
    length_bytes = struct.pack("!H", data_length)
    garbage_body = random.randbytes(data_length)
    return magic_header + length_bytes + garbage_body

def test_payload_structure():
    """測試 Payload 結構"""
    print("=" * 60)
    print("測試 1: Payload 結構驗證")
    print("=" * 60)
    
    for length in [100, 200, 300]:
        payload = generate_lazy_mimic_tls_payload(length)
        assert payload[0:3] == b'\x16\x03\x01', "Magic Header 錯誤"
        assert struct.unpack("!H", payload[3:5])[0] == length, "Length Field 錯誤"
        assert len(payload) == length + 5, "總長度錯誤"
        print(f"  ✓ 長度 {length}: Header={payload[0:3].hex()}, 前20bytes={payload[:20].hex()}")
    
    print("  ✓ 結構測試通過\n")

def test_config_parsing():
    """測試配置解析"""
    print("=" * 60)
    print("測試 2: 配置解析")
    print("=" * 60)
    
    try:
        from lib.config_module import parse_config
        cfg = parse_config("config/attacker_lazy_mimic_tls.yaml")
        
        assert cfg.simulation.packet_type == "tcp"
        assert getattr(cfg.simulation, 'tcp_attack_mode', 'syn') == "lazy_mimic_tls"
        assert "443" in cfg.simulation.target_ports
        
        print(f"  ✓ packet_type: {cfg.simulation.packet_type}")
        print(f"  ✓ tcp_attack_mode: {cfg.simulation.tcp_attack_mode}")
        print(f"  ✓ target_ports: {cfg.simulation.target_ports}\n")
        return True
    except Exception as e:
        print(f"  ✗ 配置解析失敗: {e}\n")
        return False

def test_sender_initialization():
    """測試 Sender 初始化"""
    print("=" * 60)
    print("測試 3: TCPSender 初始化")
    print("=" * 60)
    
    try:
        from lib.packet_sender import get_packet_sender
        
        # Lazy Mimic TLS 模式
        sender = get_packet_sender("tcp", "lo", tcp_attack_mode="lazy_mimic_tls")
        assert sender.tcp_attack_mode == "lazy_mimic_tls"
        print(f"  ✓ Lazy Mimic TLS 模式初始化成功")
        
        # 測試 payload 生成
        payload = sender._generate_lazy_mimic_tls_payload(200)
        assert payload[0:3] == b'\x16\x03\x01'
        print(f"  ✓ Payload 生成: {len(payload)} bytes, 前30bytes={payload[:30].hex()}\n")
        return True
    except Exception as e:
        print(f"  ✗ 初始化失敗: {e}\n")
        return False

def main():
    print("\n" + "=" * 60)
    print(" Lazy Mimic TLS 功能測試")
    print("=" * 60 + "\n")
    
    results = []
    
    # 執行測試
    test_payload_structure()
    results.append(test_config_parsing())
    results.append(test_sender_initialization())
    
    # 總結
    print("=" * 60)
    if all(results):
        print(" 所有測試通過！✓")
        print("=" * 60)
        print("\n執行命令：")
        print("  sudo python3 main.py --config config/attacker_lazy_mimic_tls.yaml\n")
        return 0
    else:
        print(" 部分測試失敗！✗")
        print("=" * 60 + "\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
