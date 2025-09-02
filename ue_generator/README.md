# UE Generator Module

此模組負責處理用戶設備（User Equipment）生成相關的功能。

## 功能

- **UE Profile 生成**: 根據配置文件生成用戶設備的配置檔案
- **流量分類**: 定義高、中、低流量等級
- **封包大小配置**: 支持均勻分布和正態分布的封包大小配置

## 主要類別

### TrafficClass
定義流量類別的枚舉：
- `HIGH`: 高流量
- `MID`: 中等流量  
- `LOW`: 低流量
- `NONE`: 無流量

### UEProfile
用戶設備配置檔案，包含：
- `id`: UE 識別碼
- `profile_name`: 配置檔案名稱
- `traffic_class`: 流量分類
- `packet_arrival_rate`: 封包到達率
- `packet_size`: 封包大小配置
- `burst`: 突發配置

### PacketSize
封包大小配置：
- `distribution`: 分布類型（uniform/normal）
- `min`: 最小大小
- `max`: 最大大小

## 主要函數

### generate_ue_profiles(config: ParsedConfig) -> List[UEProfile]
根據解析後的配置生成 UE 配置檔案列表。

## 使用範例

```python
from ue_generator import generate_ue_profiles, UEProfile, TrafficClass
from config_module import parse_config

# 載入配置
config = parse_config("config/config.yaml")

# 生成 UE 配置檔案
ue_profiles = generate_ue_profiles(config)

# 使用配置檔案
for profile in ue_profiles:
    print(f"UE {profile.id}: {profile.traffic_class.value}")
```
