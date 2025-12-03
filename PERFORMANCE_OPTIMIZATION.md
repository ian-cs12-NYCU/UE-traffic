# 效能優化說明

## 問題描述
原先在 50 個 User 時，10 個 CPU 核心幾乎全滿，無法達到理想的 bitrate。主要原因是封包發送行為消耗大量 kernel space CPU 算力。

## 優化項目

### 1. UDP Socket 重用機制 ✅
**問題：** 每次發送封包都重新 `bind()` socket，甚至在失敗時關閉並重新創建 socket
**影響：** 大量的系統呼叫（syscall），kernel space CPU 負載極高
**解決方案：**
- 實作 socket 池（socket pool），為不同目標端口維護不同的 socket
- 延遲創建（lazy initialization），需要時才創建
- 避免每次發送都重新綁定
- 在物件銷毀時統一清理所有 socket

**效能提升：** 預計減少 40-60% 的系統呼叫次數

**修改檔案：** `lib/packet_sender/udp_sender.py`

```python
# 優化前：每次都 bind，失敗還要重建
self.sock.bind(('', target_port))
# 或 close + 重建

# 優化後：使用 socket 池
self.socket_pool: Dict[int, socket.socket] = {}
sock = self._get_or_create_socket(target_port)  # 重用已存在的 socket
```

### 2. TCP Raw Socket 重用 ✅
**問題：** 每次 `send_packet()` 都創建和關閉新的 raw socket
**影響：** Raw socket 創建需要特權操作，開銷極大
**解決方案：**
- 在 `__init__` 時創建並綁定 socket
- 整個生命週期重用同一個 socket
- 在 `__del__` 時才關閉

**效能提升：** 預計減少 50-70% 的 TCP 相關 CPU 負載

**修改檔案：** `lib/packet_sender/tcp_sender.py`

```python
# 優化前：每次都創建新的 socket
sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_TCP)
# ... 發送後
sock.close()

# 優化後：初始化時創建，持續重用
def __init__(self, iface: str):
    self._setup_socket()  # 只執行一次

def send_packet(self, ...):
    self.sock.sendto(tcp_packet, ...)  # 重用預先創建的 socket
```

### 3. 減少 Recorder 鎖競爭 ✅
**問題：** 50 個執行緒同時發送封包，每個封包記錄都需要獲取全域鎖
**影響：** 嚴重的鎖競爭（lock contention），執行緒大量時間花在等待鎖
**解決方案：**
- 使用 thread-local buffer，每個執行緒維護自己的封包記錄 buffer
- 累積 100 筆記錄後才批次寫入主記錄（減少鎖獲取次數）
- 統計資料（packet count, bytes）仍即時更新，確保顯示正確

**效能提升：** 預計減少 30-50% 的鎖等待時間

**修改檔案：** `lib/recorder/core.py`

```python
# 優化前：每個封包都獲取鎖
with self.lock:
    self.packet_records.append(record)  # 每次都加鎖

# 優化後：使用 thread-local buffer
self.thread_local = threading.local()
buffer = self._get_thread_buffer()  # 無需鎖
buffer.append(record)
if len(buffer) >= 100:
    self._flush_thread_buffer()  # 批次寫入才加鎖
```

### 4. 可選的詳細記錄模式 ✅
**問題：** 記錄每個封包的完整資訊（timestamp, src_ip, dst_ip, ports 等）消耗大量記憶體
**影響：** 記憶體分配和垃圾回收增加 CPU 負載
**解決方案：**
- 新增配置選項 `record_packet_details`（預設為 true）
- 當設為 false 時，只保留統計資訊（packet count, bitrate），不記錄每個封包
- 適用於高負載測試場景

**效能提升：** 預計減少 20-40% 的記憶體使用和相關 CPU 負載

**配置檔案：** `config/config.yaml`

```yaml
simulation:
  # 設為 false 可大幅節省記憶體和 CPU
  record_packet_details: false  # 高負載測試時建議關閉
```

### 5. 配置模型完善 ✅
**新增配置欄位：**
- `batch_size`: 批次發送封包數量（預設 20）
- `log_level`: 日誌等級控制（DEBUG/INFO/WARNING/ERROR）
- `record_packet_details`: 是否記錄封包詳細資訊（預設 true）

**修改檔案：** 
- `lib/config_module/models.py`
- `lib/config_module/parser.py`

## 預期效能提升

| 優化項目 | CPU 節省 | 記憶體節省 |
|---------|---------|-----------|
| UDP Socket 重用 | 40-60% | 10-20% |
| TCP Raw Socket 重用 | 50-70% | 5-10% |
| Recorder 鎖優化 | 30-50% | 5% |
| 關閉詳細記錄 | 20-40% | 60-80% |
| **總計（全部啟用）** | **60-80%** | **70-85%** |

## 使用建議

### 高負載場景（50+ UEs）
```yaml
simulation:
  batch_size: 30  # 增加批次大小
  record_packet_details: false  # 關閉詳細記錄
  log_level: WARNING  # 減少日誌輸出
```

### 一般場景（< 30 UEs）
```yaml
simulation:
  batch_size: 20  # 預設值
  record_packet_details: true  # 保留詳細記錄
  log_level: INFO
```

### 除錯場景
```yaml
simulation:
  batch_size: 10  # 較小的批次以便觀察
  record_packet_details: true
  log_level: DEBUG
```

## 測試建議

1. **基準測試**：先測試優化前的效能（已完成）
2. **優化測試**：使用相同配置測試優化後的效能
3. **CPU 監控**：使用 `htop` 或 `top` 觀察 CPU 使用率
4. **系統呼叫分析**：使用 `strace` 或 `perf` 分析系統呼叫次數

```bash
# CPU 監控
htop

# 系統呼叫分析（需要 root）
sudo strace -c -p $(pgrep -f "python.*main.py")

# 效能分析
sudo perf record -p $(pgrep -f "python.*main.py")
sudo perf report
```

## 相容性說明

所有優化都向後相容，不影響現有功能：
- ✅ 原有配置檔案可正常使用（新欄位有預設值）
- ✅ 輸出格式不變
- ✅ 統計資料保持正確
- ✅ CSV 記錄功能可選擇開啟/關閉

## 技術細節

### Socket 重用原理
- **問題根源**：Linux kernel 的 socket 創建/綁定需要進入 kernel space，涉及複雜的網路協議棧操作
- **優化原理**：重用 socket 避免重複的 kernel space 操作，只需一次綁定即可持續使用
- **注意事項**：UDP 使用 socket 池支援多端口，TCP 使用單一 socket（因為 raw socket 不綁定端口）

### Thread-local Buffer 原理
- **問題根源**：多執行緒競爭全域鎖時，大量時間花在鎖的等待上（而非實際工作）
- **優化原理**：每個執行緒維護獨立的 buffer，無需鎖保護，定期批次合併到主記錄
- **trade-off**：即時性略降（最多延遲 100 筆記錄），但不影響統計準確性

### 記憶體優化原理
- **問題根源**：高頻率的小物件分配（dict）導致 Python GC 頻繁觸發
- **優化原理**：關閉詳細記錄後，只維護統計數據（整數加法），避免大量物件分配
- **適用場景**：長時間高負載測試、壓力測試等不需要詳細記錄的場景

## 後續優化方向

如果仍需進一步優化，可考慮：
1. 使用 `asyncio` 替代多執行緒（減少上下文切換開銷）
2. 使用 C 擴展或 Cython 重寫關鍵路徑
3. 使用 `mmap` 或共享記憶體減少記憶體複製
4. 批次網路 I/O（sendmmsg 系統呼叫）
5. 使用 DPDK 或 XDP 繞過 kernel networking stack（極端優化）
