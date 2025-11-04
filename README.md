

# UE Traffic Generator

本專案是一個用戶設備（UE）流量生成器，用於模擬多個UE的網路流量。

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

**測試網段展開功能：**
```bash
# 測試網段展開和流量分布
python3 -m lib.network_utils

# 完整的配置測試（包含流量分布統計）
python3 test_subnet_expansion.py
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
$ .venv/bin/activate
(UE-traffic) $ pip3 install -r requirements.txt 
(UE-traffic) $ sudo /home/vagrant/UE-traffic/.venv/bin/python3 main.py
```

若只需要基本多 UE ping 功能，不需要流量控制，可以使用 simple-ping/ 目錄下的 `./multiple-UE.sh`
