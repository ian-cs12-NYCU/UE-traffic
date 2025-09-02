#!/usr/bin/env python3
"""
配置模組測試腳本
"""

# 由於測試文件在模組內部，需要添加父目錄到路徑
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config_module import parse_config, display_config, ConfigHelper

def test_config_module():
    """測試配置模組功能"""
    print("=" * 60)
    print("配置模組測試")
    print("=" * 60)
    
    try:
        # 測試配置解析
        print("1. 測試配置解析...")
        config = parse_config("config/config.yaml")
        print("✅ 配置解析成功")
        
        # 顯示配置
        print("\n2. 顯示配置信息...")
        display_config(config)
        
        # 測試配置助手
        print("\n3. 測試配置助手...")
        ratios = {
            "high_traffic": 0.2,
            "mid_traffic": 0.3,
            "low_traffic": 0.5
        }
        
        print("比例分配測試 (100個UE):")
        distribution = ConfigHelper.calculate_distribution_from_ratios(100, ratios)
        print(f"分配結果: {distribution}")
        
        print("\n比例分配測試 (13個UE):")
        distribution = ConfigHelper.calculate_distribution_from_ratios(13, ratios)
        print(f"分配結果: {distribution}")
        
        # 測試YAML模板生成
        print("\n4. 生成YAML模板...")
        template = ConfigHelper.generate_config_yaml_template(50, ratios)
        print(template)
        
        print("\n✅ 所有測試通過！")
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_config_module()
