import threading
from typing import Dict, List, Optional
from datetime import datetime
import csv
import logging

from ..ue_generator import UEProfile

logger = logging.getLogger("UE-traffic")


class Recorder:
    def __init__(self, lock: threading.Lock, ueProfiles: List[UEProfile], csv_path: str = "log/packet_records.csv"):
        self.lock = lock
        self.csv_path = csv_path
        self.record_start_time = datetime.now().timestamp()

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

        # Interval 統計追蹤（用於週期性顯示）
        self.interval_start_time = datetime.now().timestamp()
        self.interval_packet_cnt: Dict[int, int] = {}  # 每個 UE 在當前 interval 的封包數
        self.interval_bytes: Dict[int, int] = {}  # 每個 UE 在當前 interval 的位元組數

        # 每個 UE 的總位元組數（即時追蹤，避免重複計算）
        self.ue_total_bytes: Dict[int, int] = {}

        for ue in ueProfiles:
            self.ue_packet_cnt[ue.id] = 0
            self.interval_packet_cnt[ue.id] = 0
            self.interval_bytes[ue.id] = 0
            self.ue_total_bytes[ue.id] = 0
        
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

            # ue total bytes (cache) record - 即時更新，避免後續遍歷
            if ue_id in self.ue_total_bytes:
                self.ue_total_bytes[ue_id] += size_bytes

            # interval statistics update
            if ue_id in self.interval_packet_cnt:
                self.interval_packet_cnt[ue_id] += 1
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
    
    def get_interval_stats(self) -> Dict[int, Dict[str, float]]:
        """
        獲取當前 interval 的統計數據
        返回格式: {ue_id: {'packets': int, 'bytes': int, 'bitrate_bps': float}}
        """
        with self.lock:
            current_time = datetime.now().timestamp()
            interval_duration = current_time - self.interval_start_time
            
            stats = {}
            for ue_id in self.interval_packet_cnt.keys():
                packets = self.interval_packet_cnt[ue_id]
                bytes_val = self.interval_bytes[ue_id]
                
                # 計算 bitrate (bits per second)
                bitrate_bps = (bytes_val * 8 / interval_duration) if interval_duration > 0 else 0
                
                stats[ue_id] = {
                    'packets': packets,
                    'bytes': bytes_val,
                    'bitrate_bps': bitrate_bps
                }
            
            return stats
    
    def reset_interval_stats(self):
        """重置 interval 統計數據"""
        with self.lock:
            self.interval_start_time = datetime.now().timestamp()
            for ue_id in self.interval_packet_cnt.keys():
                self.interval_packet_cnt[ue_id] = 0
                self.interval_bytes[ue_id] = 0
    
    def get_final_statistics(self) -> Dict:
        """
        獲取最終統計報告
        返回格式: {
            'per_ue': {ue_id: {'packets': int, 'bytes': int, 'avg_bitrate_bps': float}},
            'total': {'packets': int, 'bytes': int, 'avg_bitrate_bps': float, 'duration': float}
        }
        """
        with self.lock:
            current_time = datetime.now().timestamp()
            total_duration = current_time - self.record_start_time
            
            per_ue_stats = {}
            total_packets = 0
            total_bytes = 0
            
            for ue_id, packets in self.ue_packet_cnt.items():
                # 使用即時追蹤的位元組數，避免遍歷整個列表
                ue_bytes = self.ue_total_bytes.get(ue_id, 0)
                
                # 計算平均 bitrate
                avg_bitrate = (ue_bytes * 8 / total_duration) if total_duration > 0 else 0
                
                per_ue_stats[ue_id] = {
                    'packets': packets,
                    'bytes': ue_bytes,
                    'avg_bitrate_bps': avg_bitrate
                }
                
                total_packets += packets
                total_bytes += ue_bytes
            
            total_avg_bitrate = (total_bytes * 8 / total_duration) if total_duration > 0 else 0
            
            return {
                'per_ue': per_ue_stats,
                'total': {
                    'packets': total_packets,
                    'bytes': total_bytes,
                    'avg_bitrate_bps': total_avg_bitrate,
                    'duration': total_duration
                }
            }
        
    