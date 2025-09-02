

# UE Traffic Generator

本專案是一個用戶設備（UE）流量生成器，用於模擬多個UE的網路流量。

## 專案結構

```
.
├── config/                 # 配置文件
├── config_module/          # 配置解析模組
├── ue_generator/          # UE生成器模組
├── packet_sender/         # 封包發送模組
├── traffic_replayer/      # 流量重播模組
├── UDP_server/           # UDP伺服器
├── simple-ping/          # 簡單ping功能
├── main.py               # 主程式入口
├── simulator.py          # 模擬器核心
├── recorder.py           # 記錄器
└── display.py            # 顯示功能
```

## How to Start

在啟動本程式前，先
* 開啟free5gc核心網路
* 透過 UERANSIM 建立好對應數量的UE


* ping3 module 所使用的為 raw socket。
* uesimtunX 被kernel 限制一般使用者 SO_BINDTODEVICE 行為
因此需要root權限

``` 
sudo pip3 install -r requirement.txt
sudo python3 main.py
```

若只需要基本多UE ping 功能，不需要流量控制，可以使用 simple-ping/ 目錄下的 ```./multilple.sh```

### UDP 版本

### 架構
