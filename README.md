

# UE Traffic Generator

本專案是一個用戶設備（UE）流量生成器，用於模擬多個UE的網路流量。

## 📌 新功能：Lazy Mimic TLS 攻擊模式

支援偽造 TLS 握手的攻擊模式，用於學術研究測試 LLM 防禦系統。

**快速使用：**
```bash
# 測試 Payload 生成
python3 test_lazy_mimic_tls.py

# 集成測試
python3 test_integration_lazy_mimic_tls.py

# 實際運行
sudo python3 main.py --config config/attacker_lazy_mimic_tls.yaml
```

**配置方式：**
```yaml
simulation:
  packet_type: tcp
  tcp_attack_mode: lazy_mimic_tls  # 或 syn (預設)
  target_ports: "443"
```

**技術細節：**
- Payload 結構：`[0x16 0x03 0x01] + [Length (2 bytes)] + [Random Garbage]`
- 欺騙簡單 DPI，但 Wireshark 會顯示 "Malformed Packet"
- 適合 LLM 測試，建議 PPS 100-200（SYN 模式可達 500+）

詳見 [PERFORMANCE_OPTIMIZATION.md](PERFORMANCE_OPTIMIZATION.md) 中的 "TCP 攻擊模式效能差異" 章節。

## 專案結構

```
.
├── config/                 # 配置文件
│   └── config.yaml         # 主配置文件（支援 CIDR 網段）
├── lib/                    # 核心程式庫
│   ├── config_module/      # 配置解析模組
│   ├── ue_generator/       # UE生成器模組
│   ├── packet_sender/      # 封包發送模組
│   ├── simulator/          # 模擬器模組
│   ├── network_utils.py    # 網路工具（CIDR 網段展開）
│   ├── recorder.py         # 記錄器
│   └── display.py          # 顯示功能
├── test_subnet_expansion.py    # 網段配置測試腳本
├── UDP_server/             # UDP伺服器
├── simple-ping/            # 簡單ping功能
├── main.py                 # 主程式入口
└── requirements.txt        # 相依套件
```

## 配置說明

### 目標網段配置 (Target Subnets)

本程式支援使用 CIDR 網段表示法指定目標 IP 地址。流量會**均勻分布**到網段內的所有可用 IP 地址上。

在 `config/config.yaml` 中配置：

```yaml
simulation:
  target_subnets:
    - 10.201.10.0/24      # 254 個可用 IP (10.201.10.1 ~ 10.201.10.254)
    - 192.168.1.0/24      # 254 個可用 IP (192.168.1.1 ~ 192.168.1.254)
    - 8.8.8.8/32          # 單個 IP (8.8.8.8)
```

### 目標端口配置 (Target Ports)

支援靈活的端口配置方式，流量會**均勻分布**到所有指定的端口上。

**配置格式：**

```yaml
simulation:
  target_ports: "80, 443, 8000-8010, 9000"
```

**支援的格式：**
- 單個端口：`"80"`
- 多個端口：`"80, 443, 8080"`
- 端口範圍：`"8000-8010"` (包含起始和結束端口)
- 混合使用：`"80, 443, 8000-8010, 9000"`

**配置範例：**

```yaml
# 範例 1: 常見 Web 端口
target_ports: "80, 443, 8080, 8443"

# 範例 2: 測試端口範圍
target_ports: "9000-9010"

# 範例 3: 混合配置
target_ports: "53, 80, 443, 3000-3005, 8080, 9000-9002"
```

**測試配置功能：**
```bash
# 測試網段展開和流量分布
python3 -m lib.network_utils

# 測試端口解析和流量分布
python3 -m lib.port_utils

# 完整的配置測試（包含流量分布統計）
python3 test_subnet_expansion.py
```

## TCP 攻擊模式 (TCP Attack Modes)

本專案支援兩種 TCP 攻擊模式，用於模擬不同類型的網路攻擊行為：

### 1. SYN Flood 攻擊 (預設)

**配置方式：**
```yaml
simulation:
  packet_type: tcp
  tcp_attack_mode: syn  # 或省略此選項（預設為 syn）
```

**行為特徵：**
- 只發送 TCP SYN 封包，不完成三次握手
- 使用 raw socket 直接發送封包
- 適合模擬傳統的 SYN flood DDoS 攻擊

### 2. Lazy Mimic TLS 攻擊 (偽造 TLS)

**配置方式：**
```yaml
simulation:
  packet_type: tcp
  tcp_attack_mode: lazy_mimic_tls
  target_ports: "443"  # 通常針對 HTTPS 端口
```

**行為特徵：**
- 完成 TCP 三次握手（建立正常連線）
- 發送偽造的 TLS Client Hello 封包
- Payload 結構：`[0x16 0x03 0x01] + [Length] + [Random Garbage]`
- 立即斷線，不等待伺服器回應

**技術細節：**
- **Magic Header**: `16 03 01` (TLS Handshake + TLS 1.0)
- **Length Field**: 2 bytes, Big-Endian，記錄後續隨機資料長度
- **Garbage Body**: 完全隨機的垃圾資料（非真實的 TLS Client Hello）

**Wireshark 表現：**
- Protocol 欄位顯示為 "TLSv1" 或 "SSL"
- 詳細資訊會顯示 "Malformed Packet" 或解析錯誤
- 原因：Handshake Type (第 6 byte) 不是 `0x01` (Client Hello)

**應用場景：**
用於測試防禦系統（如 LLM）是否能透過分析 Payload 結構來識別偽造的 TLS 流量，
而不僅僅依賴簡單的 DPI (Deep Packet Inspection)。

**示例配置：** 參見 [config/attacker_lazy_mimic_tls.yaml](config/attacker_lazy_mimic_tls.yaml)

**測試工具：**
```bash
# 測試 Lazy Mimic TLS payload 生成邏輯
python3 test_lazy_mimic_tls.py
```

## How to Start

在啟動本程式前，先：
* 開啟 free5gc 核心網路
* 透過 UERANSIM 或 PacketRusher 建立好對應數量的 UE

**注意事項：**
* ping3 module 使用 raw socket
* uesimtunX / valXXXXXXXXXX 介面被 kernel 限制一般使用者的 SO_BINDTODEVICE 行為
* 因此需要 root 權限

**安裝與執行：**
``` 
sudo pip3 install -r requirements.txt
sudo python3 main.py
```

或是在 venv 中使用：
```bash
$ python3 -m venv --prompt UE-traffic .venv
$ source .venv/bin/activate
(UE-traffic) $ pip3 install -r requirements.txt 
(UE-traffic) $ sudo /home/vagrant/UE-traffic/.venv/bin/python3 main.py

// 指定不同的配置檔
(UE-traffic) $ sudo /home/vagrant/UE-traffic/.venv/bin/python3 main.py --config config/config_50_percent_burst.yaml
(UE-traffic) $ sudo /home/vagrant/UE-traffic/.venv/bin/python3 main.py --config config/config_80_percent_burst.yaml
(UE-traffic) $ sudo /home/vagrant/UE-traffic/.venv/bin/python3 main.py --config config/traditional_DDoS.yaml
(UE-traffic) $ sudo /home/vagrant/UE-traffic/.venv/bin/python3 main.py --config config/attacker_lazy_mimic_tls.yaml
```

若只需要基本多 UE ping 功能，不需要流量控制，可以使用 simple-ping/ 目錄下的 `./multiple-UE.sh`
