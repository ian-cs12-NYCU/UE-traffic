import threading
from typing import Dict, List
from ue_generator import UEProfile


class Recorder:
    def __init__(self, lock: threading.Lock, ueProfiles: List[UEProfile]):
        self.lock = lock

        # example 0:15  -> id=0 UE send 15 packets
        self.ue_packet_cnt: Dict[int, int] = {}
        for ue in ueProfiles:
            self.ue_packet_cnt[ue.id] = 0
        
        print(f"[INFO] Recorder initialized with {len(self.ue_packet_cnt)} UEs.")

    def increment(self, ue_id: int):
        with self.lock:
            self.ue_packet_cnt[ue_id] += 1

    def get_record(self):
        with self.lock:
            return self.ue_packet_cnt.copy()