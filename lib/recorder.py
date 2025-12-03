import threading
from typing import Dict, List, Optional
from datetime import datetime
import csv
import time
import logging

from .ue_generator import UEProfile

logger = logging.getLogger("UE-traffic")


class Recorder:
    def __init__(self, lock: threading.Lock, ueProfiles: List[UEProfile], csv_path: str = "log/packet_records.csv"):
        self.lock = lock
        self.csv_path = csv_path
        self.record_start_time = datetime.now().timestamp()
        
        # 用於追蹤 interval 統計
        self.last_interval_time = self.record_start_time
        self.interval_packet_count: Dict[int, int] = {}  # 每個 interval 的封包數
        self.interval_bytes: Dict[int, int] = {}  # 每個 interval 的位元組數

        # 紀錄每一個送出的封包資訊，用於畫圖 / 儲存 CSV / 時間分析
        # 每筆紀錄是一個字典，格式如下：
        # {
        #     "timestamp": float,    # 封包送出時間（timestamp in seconds）
        #     "ue_id": int,          # 發送封包的 UE ID（對應 UEProfile.id）
        #     "iface": str,          # Interface 名稱，例如 "uesimtun1"
        #     "size_bytes": int,     # 封包大小（byte）
        #     "latency_ms": float    # ping latency（毫秒），可為 None
        # }
        self.packet_records: List[Dict] = []

        # 每個 UE 已發送的封包總數，用於：
        # - 即時畫面（bar chart 條狀圖）
        # - 模擬後快速統計每個 UE 的發送強度
        # 結構範例如下：
        # {
        #     1: 47,   # UE 1 發了 47 個封包
        #     2: 58,   # UE 2 發了 58 個封包
        #     ...
        # }
        self.ue_packet_cnt: Dict[int, int] = {}
        
        # 每個 UE 已發送的總位元組數
        self.ue_total_bytes: Dict[int, int] = {}

        # 每個 UE 所送封包的延遲（latency）記錄，用於：
        # - 延遲分析（平均 / 標準差 / 最大最小）
        # - 畫 latency boxplot（橫向比較各 UE）
        # 結構範例如下：
        # {
        #     1: [3.12, 2.95, 3.48, ...],
        #     2: [12.1, 11.8, 14.3, ...],
        #     ...
        # }
        self.ue_latency_ms: Dict[int, List[float]] = {}

        for ue in ueProfiles:
            self.ue_packet_cnt[ue.id] = 0
            self.ue_total_bytes[ue.id] = 0
            self.interval_packet_count[ue.id] = 0
            self.interval_bytes[ue.id] = 0
        
        logger.info(f"Recorder initialized with {len(self.ue_packet_cnt)} UEs.")

    def record_packet(
        self,
        ue_id: int,
        iface: str,
        size_bytes: int,
        src_ip: str,
        dst_ip: str,
        src_port: Optional[int] = None,
        dst_port: Optional[int] = None,
        latency_ms: Optional[float] = None
    ):
        with self.lock:
            self.packet_records.append({
                "timestamp": datetime.now().timestamp() - self.record_start_time,
                "ue_id": ue_id,
                "iface": iface,
                "size_bytes": size_bytes,
                "latency_ms": latency_ms,
                "src_ip": src_ip,
                "dst_ip": dst_ip,
                "src_port": src_port,
                "dst_port": dst_port
            })

            # ue packet cnt (cache) record
            self.ue_packet_cnt[ue_id] += 1
            self.ue_total_bytes[ue_id] += size_bytes
            
            # interval 統計
            self.interval_packet_count[ue_id] += 1
            self.interval_bytes[ue_id] += size_bytes

            # ue latency ms (cache) record
            if latency_ms is not None:
                if ue_id not in self.ue_latency_ms:
                    self.ue_latency_ms[ue_id] = []
                self.ue_latency_ms[ue_id].append(latency_ms)
    
    def save_csv(self):
        if not self.packet_records:
            logger.error("No packet records to save.")
            return
        
        # 印出self.packet_records前幾行
        for record in self.packet_records[:5]:
            logger.debug(f"Packet Record: {record}")

        with open(self.csv_path, "w", newline="") as csvfile:
            fieldnames = self.packet_records[0].keys()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for record in self.packet_records:
                writer.writerow(record)

    def get_ue_packet_cnt(self):
        with self.lock:
            return self.ue_packet_cnt.copy()
    
    def reset_interval_stats(self):
        """重置 interval 統計"""
        with self.lock:
            self.last_interval_time = time.time()
            for ue_id in self.interval_packet_count:
                self.interval_packet_count[ue_id] = 0
                self.interval_bytes[ue_id] = 0
    
    def get_interval_stats(self):
        """獲取當前 interval 的統計數據"""
        with self.lock:
            current_time = time.time()
            interval_duration = current_time - self.last_interval_time
            
            stats = {}
            for ue_id in self.ue_packet_cnt:
                packet_count = self.interval_packet_count[ue_id]
                total_bytes = self.interval_bytes[ue_id]
                
                # 計算 bitrate (bits per second)
                bitrate_bps = (total_bytes * 8 / interval_duration) if interval_duration > 0 else 0
                
                stats[ue_id] = {
                    'packets': packet_count,
                    'bytes': total_bytes,
                    'bitrate_bps': bitrate_bps,
                    'duration': interval_duration
                }
            
            return stats
    
    def get_final_statistics(self):
        """獲取最終統計報告"""
        with self.lock:
            current_time = time.time()
            total_duration = current_time - self.record_start_time
            
            stats = {}
            total_packets = 0
            total_bytes = 0
            
            for ue_id in self.ue_packet_cnt:
                packet_count = self.ue_packet_cnt[ue_id]
                total_bytes_ue = self.ue_total_bytes[ue_id]
                
                # 計算平均 bitrate
                avg_bitrate_bps = (total_bytes_ue * 8 / total_duration) if total_duration > 0 else 0
                
                stats[ue_id] = {
                    'packets': packet_count,
                    'bytes': total_bytes_ue,
                    'avg_bitrate_bps': avg_bitrate_bps
                }
                
                total_packets += packet_count
                total_bytes += total_bytes_ue
            
            # 總體統計
            total_bitrate_bps = (total_bytes * 8 / total_duration) if total_duration > 0 else 0
            
            return {
                'per_ue': stats,
                'total': {
                    'packets': total_packets,
                    'bytes': total_bytes,
                    'avg_bitrate_bps': total_bitrate_bps,
                    'duration': total_duration
                }
            }
    
    