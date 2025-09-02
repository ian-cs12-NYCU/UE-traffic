# UE Traffic Generator Library

這個目錄包含了 UE Traffic Generator 的所有核心模組和功能。

## 模組結構

### 核心模組
- **`config_module/`**: 配置文件解析和管理
- **`ue_generator/`**: 用戶設備生成器
- **`packet_sender/`**: 封包發送器（支援 UDP、TCP、Ping）

### 核心功能
- **`simulator.py`**: 主要的模擬器邏輯，協調所有 UE 的流量生成
- **`recorder.py`**: 記錄和追蹤封包傳送的統計資料
- **`display.py`**: 即時顯示和視覺化功能

## 使用方式

從主目錄導入模組：

```python
from lib.config_module import parse_config
from lib.ue_generator import generate_ue_profiles
from lib.simulator import Simulator
```

## 模組相依性

```
main.py
├── lib.config_module
├── lib.ue_generator
└── lib.simulator
    ├── lib.config_module
    ├── lib.packet_sender
    ├── lib.ue_generator
    ├── lib.display
    └── lib.recorder
```

這個架構確保了：
1. 清晰的模組分離
2. 良好的相依性管理
3. 易於維護和擴展的程式碼結構
