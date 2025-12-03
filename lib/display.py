import os
import time
import threading
import pandas as pd
import matplotlib.pyplot as plt
import logging

from .recorder import Recorder

logger = logging.getLogger("UE-traffic")


def format_bitrate(bitrate_bps: float) -> str:
    """將 bitrate 格式化為易讀的單位 (bps, Kbps, Mbps)"""
    if bitrate_bps >= 1_000_000:
        return f"{bitrate_bps / 1_000_000:.2f} Mbps"
    elif bitrate_bps >= 1_000:
        return f"{bitrate_bps / 1_000:.2f} Kbps"
    else:
        return f"{bitrate_bps:.2f} bps"


def format_bytes(bytes_val: int) -> str:
    """將位元組數格式化為易讀的單位 (B, KB, MB)"""
    if bytes_val >= 1_000_000:
        return f"{bytes_val / 1_000_000:.2f} MB"
    elif bytes_val >= 1_000:
        return f"{bytes_val / 1_000:.2f} KB"
    else:
        return f"{bytes_val} B"


class Display:
    def __init__(self, recorder: Recorder, lock: threading.Lock,  interval: float = 1.0):
        self.recorder = recorder
        self.interval = interval
        self.lock = lock
    
    def start_live_bar_chart(self):
        """
        Start a live bar chart display of UE packet counts with interval statistics.
        """
        while True:
            os.system('clear')
            
            # 獲取 interval 統計數據
            interval_stats = self.recorder.get_interval_stats()
            
            print("=" * 80)
            print(f"{'UE Traffic Monitor':^80}")
            print("=" * 80)
            print(f"{'UE ID':<8} {'Packets':<12} {'Data Size':<15} {'Bitrate':<15}")
            print("-" * 80)
            
            total_packets = 0
            total_bytes = 0
            total_bitrate = 0.0
            
            for ue_id, stats in sorted(interval_stats.items()):
                packets = stats['packets']
                bytes_val = stats['bytes']
                bitrate = stats['bitrate_bps']
                
                total_packets += packets
                total_bytes += bytes_val
                total_bitrate += bitrate
                
                print(f"UE {ue_id:<5} {packets:<12} {format_bytes(bytes_val):<15} {format_bitrate(bitrate):<15}")
            
            print("-" * 80)
            print(f"{'TOTAL':<8} {total_packets:<12} {format_bytes(total_bytes):<15} {format_bitrate(total_bitrate):<15}")
            print("=" * 80)
            
            # 重置 interval 統計
            self.recorder.reset_interval_stats()
            
            time.sleep(self.interval)
    def plot_scatter_plot(self, csv_path: str = "log/packet_records.csv", save_path: str = "images/packet_timeline.png"):
        try:
            df = pd.read_csv(csv_path)
        except Exception as e:
            logger.error(f"Failed to read CSV: {e}")
            return

        required_cols = {"timestamp", "ue_id", "size_bytes"}
        if not required_cols.issubset(df.columns):
            logger.error("CSV file missing required columns.")
            return

        # 數值轉換與清洗
        df = df.dropna(subset=["timestamp", "ue_id", "size_bytes"])
        df["size_bytes"] = pd.to_numeric(df["size_bytes"], errors="coerce")
        df["ue_id"] = pd.to_numeric(df["ue_id"], errors="coerce").astype("Int64")
        
        # 點大小標準化
        min_size = df["size_bytes"].min()
        max_size = df["size_bytes"].max()
        df["point_size"] = 10 + 90 * (df["size_bytes"] - min_size) / (max_size - min_size + 1e-6)

        # 轉換時間格式（可選）
        df["time_readable"] = pd.to_datetime(df["timestamp"], unit="s")

        # 畫圖
        plt.figure(figsize=(12, 6))
        plt.scatter(
            x=df["time_readable"],
            y=df["ue_id"],
            s=df["point_size"],
            c=df["ue_id"],
            cmap="tab10",
            alpha=0.3,
            marker="s",
        )
        plt.xlabel("Time")
        plt.ylabel("UE ID")
        plt.title("Packet Send Timeline per UE (Dot Size = Packet Size)")
        plt.xticks(rotation=30)
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(save_path, dpi=300)
        logger.info(f"Packet timeline scatter plot saved to {save_path}")

    def plot_scatter_and_volume_bar(
            self,
            csv_path="log/packet_records.csv", 
            save_path="images/scatter_volume_subplot.png"):
        df = pd.read_csv(csv_path)
        df = df.dropna(subset=["timestamp", "ue_id", "size_bytes"])
        df["timestamp"] = pd.to_numeric(df["timestamp"], errors="coerce")
        df["size_bytes"] = pd.to_numeric(df["size_bytes"], errors="coerce")
        df["ue_id"] = pd.to_numeric(df["ue_id"], errors="coerce").astype("Int64")
        df["time_readable"] = pd.to_datetime(df["timestamp"], unit="s")

        # Normalize dot size
        min_size = df["size_bytes"].min()
        max_size = df["size_bytes"].max()
        df["point_size"] = 10 + 90 * (df["size_bytes"] - min_size) / (max_size - min_size + 1e-6)

        # Volume sum
        ue_volume = df.groupby("ue_id")["size_bytes"].sum()

        # Plot
        fig, (ax1, ax2) = plt.subplots(nrows=2, figsize=(12, 8), gridspec_kw={'height_ratios': [3, 1]}, sharex=False)

        # Scatter plot (Time vs UE ID)
        ax1.scatter(
            df["time_readable"],
            df["ue_id"],
            s=df["point_size"],
            c=df["ue_id"],
            cmap="tab10",
            alpha=0.6,
            marker="s"
        )
        ax1.set_title("Packet Timeline per UE")
        ax1.set_ylabel("UE ID")
        ax1.grid(True)

        # Bar chart (UE ID vs Total Volume)
        ax2.bar(
            ue_volume.index.astype(str),
            ue_volume.values,
            color="gray",
            alpha=0.6
        )
        ax2.set_ylabel("Total Volume (bytes)")
        ax2.set_xlabel("UE ID")
        ax2.set_title("Total Sent Volume per UE")
        ax2.grid(True, axis='y')

        plt.tight_layout()
        plt.savefig(save_path, dpi=300)
        logger.info(f"Scatter + volume bar saved to {save_path}")
    
    def print_final_statistics(self):
        """打印最終統計報告"""
        stats = self.recorder.get_final_statistics()
        
        print("\n" + "=" * 80)
        print(f"{'FINAL STATISTICS REPORT':^80}")
        print("=" * 80)
        print(f"{'UE ID':<8} {'Total Packets':<15} {'Total Data':<15} {'Avg Bitrate':<15}")
        print("-" * 80)
        
        for ue_id, ue_stats in sorted(stats['per_ue'].items()):
            packets = ue_stats['packets']
            bytes_val = ue_stats['bytes']
            bitrate = ue_stats['avg_bitrate_bps']
            
            print(f"UE {ue_id:<5} {packets:<15} {format_bytes(bytes_val):<15} {format_bitrate(bitrate):<15}")
        
        print("-" * 80)
        total = stats['total']
        print(f"{'TOTAL':<8} {total['packets']:<15} {format_bytes(total['bytes']):<15} {format_bitrate(total['avg_bitrate_bps']):<15}")
        print("=" * 80)
        print(f"Total Duration: {total['duration']:.2f} seconds")
        print("=" * 80)
