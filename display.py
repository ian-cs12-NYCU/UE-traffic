import os
import time
import threading
import pandas as pd
import matplotlib.pyplot as plt

from recorder import Recorder


class Display:
    def __init__(self, recorder: Recorder, lock: threading.Lock,  interval: float = 1.0):
        self.recorder = recorder
        self.interval = interval
        self.lock = lock
    
    def start_live_bar_chart(self):
        """
        Start a live bar chart display of UE packet counts.
        """
        while True:
            os.system('clear')
            print("UE Packet Count Monitor")
            print("=" * 40)
            ue_packet_cnt = self.recorder.get_ue_packet_cnt()
            
            for id, cnt in ue_packet_cnt.items():
                bar = "▇" * max(0, cnt // 2)
                print(f"UE {id:<12}: {bar:<40} {cnt} pkt")
            time.sleep(self.interval)
    def plot_scatter_plot(self, csv_path: str = "log/packet_records.csv", save_path: str = "images/packet_timeline.png"):
        try:
            df = pd.read_csv(csv_path)
        except Exception as e:
            print(f"[ERROR] Failed to read CSV: {e}")
            return

        required_cols = {"timestamp", "ue_id", "size_bytes"}
        if not required_cols.issubset(df.columns):
            print("[ERROR] CSV file missing required columns.")
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
        print(f"[Display] Packet timeline scatter plot saved to {save_path}")

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
        print(f"[Display] Scatter + volume bar saved to {save_path}")