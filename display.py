import os
import time
from recorder import Recorder
import threading

class Display:
    def __init__(self, recorder: Recorder, lock: threading.Lock,  interval: float = 1.0):
        self.recorder = recorder
        self.interval = interval
        self.lock = lock

    def start_display(self):
        while True:
            os.system('clear')
            print("UE Packet Count Monitor")
            print("=" * 40)
            ue_packet_cnt = self.recorder.get_record()
            
            for id, cnt in ue_packet_cnt.items():
                bar = "▇" * max(0, cnt // 2)
                print(f"UE {id:<12}: {bar:<40} {cnt} pkt")
            time.sleep(self.interval)

