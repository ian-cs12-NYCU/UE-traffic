import os
import time

def display_stats(ue_counters: dict, lock, interval: float = 1.0):
    while True:
        os.system('clear')
        print("UE Packet Count Monitor")
        print("=" * 40)
        with lock:
            for iface, count in sorted(ue_counters.items()):
                bar = "▇" * max(0, count // 2)
                print(f"{iface:<12}: {bar:<40} {count} pkt")
        time.sleep(interval)
