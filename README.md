

在啟動本程式前，先
* 開啟free5gc核心網路
* 透過 UERANSIM 建立好對應數量的UE

TODO: 目前還未檢查interface 數量 < config要求數量情境


* ping3 module 所使用的為 raw socket。
* uesimtunX 被kernel 限制一般使用者 SO_BINDTODEVICE 行為
因此需要root權限

```
sudo pip3 install -r requirement.txt
sudo python3 main.py
```

### UDP 版本

### 架構
