# 配置模組 (config_module)

這個模組負責處理 UE 流量模擬器的配置文件解析和管理。

## 模組結構

```
config_module/
├── __init__.py      # 模組入口，導出主要接口
├── models.py        # 數據模型定義
├── parser.py        # 配置文件解析器
├── helper.py        # 配置助手工具
└── display.py       # 配置顯示工具
```

## 主要功能

### 1. 配置解析
```python
from config_module import parse_config

config = parse_config("config/config.yaml")
```

### 2. 配置顯示
```python
from config_module import display_config

display_config(config)
```

### 3. 比例分配助手
```python
from config_module import ConfigHelper

# 根據比例計算精確分配
ratios = {"high_traffic": 0.2, "mid_traffic": 0.3, "low_traffic": 0.5}
distribution = ConfigHelper.calculate_distribution_from_ratios(100, ratios)

# 生成配置模板
template = ConfigHelper.generate_config_yaml_template(100, ratios)
```

## 配置文件格式

```yaml
ue:
  allocation:
    total_count: 8              # 總UE數量
    distribution:               # 精確分配
      high_traffic: 1
      mid_traffic: 2
      low_traffic: 5
  profiles:                     # 流量特性定義
    - name: high_traffic
      packet_arrival_rate: 20
      packet_size:
        distribution: uniform
        min: 80
        max: 160
      burst:
        enable: true
        # ... burst 設定
```

## 優勢

1. **模組化設計**：配置相關功能集中管理
2. **清晰分工**：解析、顯示、助手功能分離
3. **易於擴展**：新功能可以輕易添加
4. **類型安全**：使用 dataclass 保證數據結構
5. **驗證完整**：配置一致性自動驗證
