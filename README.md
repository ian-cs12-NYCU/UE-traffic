
因為...
＊ ping3 module 所使用的為 raw socket。
＊ uesimtunX 被kernel 限制一般使用者 SO_BINDTODEVICE 行為
因此需要root權限

```
sudo pip3 install -r requirement.txt
sudo python3 main.py
```

### UDP 版本