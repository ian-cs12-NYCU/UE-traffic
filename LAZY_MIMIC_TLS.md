# Lazy Mimic TLS 攻擊模式

## 快速使用

```bash
# 測試功能
python3 test_lazy_mimic_tls.py

# 執行攻擊
sudo python3 main.py --config config/attacker_lazy_mimic_tls.yaml

# Wireshark 驗證
sudo tcpdump -i ueTun45 -w capture.pcap port 443
wireshark capture.pcap  # 應看到 TLSv1 + Malformed Packet
```

## 配置方式

```yaml
simulation:
  packet_type: tcp
  tcp_attack_mode: lazy_mimic_tls  # syn (預設) / lazy_mimic_tls
  target_ports: "443"
```

## 技術細節

**Payload 結構：**
```
[0x16 0x03 0x01] + [Length (2 bytes, Big-Endian)] + [Random Garbage]
```

- Byte 0: `0x16` - TLS Handshake
- Byte 1-2: `0x03 0x01` - TLS 1.0
- Byte 3-4: Payload 長度
- Byte 5+: 隨機垃圾資料

**效果：**
- 欺騙簡單 DPI（會認為是 TLS 流量）
- Wireshark 顯示 "Malformed Packet"（因為不是真正的 Client Hello）
- 適合測試 LLM 是否能識別偽造流量

**效能建議：**
- PPS: 100-200（SYN 模式可達 500+）
- `batch_size`: 40
- `record_packet_details`: false

更多細節見 [PERFORMANCE_OPTIMIZATION.md](PERFORMANCE_OPTIMIZATION.md)
