"""
配置助手工具
"""

from typing import Dict
from .models import UEAllocation

class ConfigHelper:
    """配置助手類，提供便利方法生成配置"""
    
    @staticmethod
    def calculate_distribution_from_ratios(total_count: int, ratios: Dict[str, float]) -> Dict[str, int]:
        """
        根據比例計算精確的UE分配
        
        Args:
            total_count: 總UE數量
            ratios: 比例字典，例如 {"high_traffic": 0.2, "mid_traffic": 0.3, "low_traffic": 0.5}
        
        Returns:
            精確分配字典
            
        Raises:
            ValueError: 當比例總和不為1.0時
        """
        # 驗證比例總和
        total_ratio = sum(ratios.values())
        if abs(total_ratio - 1.0) > 0.001:
            raise ValueError(f"比例總和必須為1.0，當前為 {total_ratio}")
        
        # 計算基礎分配
        distribution = {}
        allocated = 0
        
        # 先按比例分配整數部分
        for name, ratio in ratios.items():
            count = int(total_count * ratio)
            distribution[name] = count
            allocated += count
        
        # 處理剩餘的UE（由於整數截斷產生）
        remaining = total_count - allocated
        if remaining > 0:
            # 按照小數部分大小分配剩餘的UE
            fractional_parts = []
            for name, ratio in ratios.items():
                fractional_part = (total_count * ratio) - distribution[name]
                fractional_parts.append((fractional_part, name))
            
            # 按小數部分降序排列，優先分配給小數部分大的類型
            fractional_parts.sort(reverse=True)
            
            for i in range(remaining):
                name = fractional_parts[i][1]
                distribution[name] += 1
        
        return distribution
    
    @staticmethod
    def create_allocation_from_ratios(total_count: int, ratios: Dict[str, float]) -> UEAllocation:
        """
        根據比例創建UEAllocation對象
        
        Args:
            total_count: 總UE數量
            ratios: 比例字典
            
        Returns:
            UEAllocation對象
        """
        distribution = ConfigHelper.calculate_distribution_from_ratios(total_count, ratios)
        return UEAllocation(total_count=total_count, distribution=distribution)
    
    @staticmethod
    def generate_config_yaml_template(total_count: int, ratios: Dict[str, float]) -> str:
        """
        生成配置YAML模板字符串
        
        Args:
            total_count: 總UE數量
            ratios: 比例字典
            
        Returns:
            YAML配置模板字符串
        """
        distribution = ConfigHelper.calculate_distribution_from_ratios(total_count, ratios)
        
        lines = []
        lines.append(f"# 總UE數: {total_count}")
        lines.append(f"# 比例: {ratios}")
        lines.append("# 計算結果:")
        for name, ratio in ratios.items():
            lines.append(f"#   {name}: {ratio:.1%} -> {distribution[name]}個")
        lines.append("")
        lines.append("ue:")
        lines.append("  allocation:")
        lines.append(f"    total_count: {total_count}")
        lines.append("    distribution:")
        for name, count in distribution.items():
            lines.append(f"      {name}: {count}")
        
        return "\n".join(lines)
    
    @staticmethod
    def validate_allocation(allocation: UEAllocation) -> bool:
        """
        驗證UE分配是否有效
        
        Args:
            allocation: UEAllocation對象
            
        Returns:
            bool: 是否有效
        """
        distributed_total = sum(allocation.distribution.values())
        return distributed_total == allocation.total_count
