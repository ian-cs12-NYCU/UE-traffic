import socket
import pandas as pd
import time
import random

class TrafficReplayer:
    def __init__(self, csv_path: str, iface: str = None):
        self.df = pd.read_csv(csv_path)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        if iface:
            try:
                self.sock.setsockopt(socket.SOL_SOCKET, 25, iface.encode())
            except PermissionError:
                print(f"[WARN] Cannot bind to iface '{iface}' (need root)")

    def replay(self):
        # 轉換時間欄位為相對秒數（例如 33:10.6 → 秒）
        self.df["Time"] = self.df["Time"].apply(self._parse_time)
        self.df.sort_values("Time", inplace=True)

        print(f"self.df.head(3) = {self.df.head(3)}\n\n\n")
        print(f"self.df.columns = {self.df.columns}\n\n\n")
        print(f"self.df.dtypes = {self.df.dtypes}\n\n\n")

        base_time = self.df["Time"].min()
        start_wall = time.time()

        # for _, row in self.df.iterrows():
        #     send_time = start_wall + (row["Time"] - base_time)
        #     wait = send_time - time.time()
        #     if wait > 0:
        #         time.sleep(wait)

        #     size = int(row["Length"])
        #     dst = row["Destination"]
        #     payload = bytes(random.getrandbits(8) for _ in range(size))

        #     try:
        #         self.sock.sendto(payload, (dst, 9000))  # 預設 UDP port，可再動態調整 TODO:
        #         print(f"[SEND] {size} bytes to {dst}")
        #     except Exception as e:
        #         print(f"[ERROR] Failed to send to {dst}: {e}")

    def _parse_time(self, s: str) -> float:
        """
            將時間字串轉換為秒數
            例如 "33:10.6" 轉換為 1990.6 秒
        """
        try:
            minute, rest = s.split(":")
            return int(minute) * 60 + float(rest)
        except:
            return 0.0


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Replay network traffic from a CSV file.")
    parser.add_argument("csv_path", type=str, help="Path to the CSV file containing traffic data.")
    parser.add_argument("--iface", type=str, help="Network interface to bind to (optional).")

    args = parser.parse_args()

    replayer = TrafficReplayer(args.csv_path, args.iface)
    replayer.replay()