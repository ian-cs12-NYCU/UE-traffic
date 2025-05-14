import subprocess
import os
from datetime import datetime


def send_ping(iface: str, target_ip: str, payload_size: int, counter_dict: dict, lock, log_latency: bool = False, latency_dict: dict = None):
    if not os.path.exists(f"/sys/class/net/{iface}"):
        print(f"[ERROR] Network interface '{iface}' does not exist.")
        return

    try:
        result = subprocess.run(
            ["ping", "-I", iface, "-c", "1", "-W", "1", target_ip, "-s", str(payload_size)],
            capture_output=True,
            text=True
        )
        now = datetime.now().timestamp()
        
        if result.returncode == 0: # Successful ping
            # example ping output: "64 bytes from 8.8.8.8: icmp_seq=1 ttl=116 time=4.33 ms"
            for line in result.stdout.split("\n"): # acquired latency
                if "time=" in line:
                    time_part = line.split("time=")[-1]
                    latency = float(time_part.split(" ")[0])
                    if log_latency and latency_dict is not None:
                        with lock:
                            latency_dict[iface].append((now, latency))
                    break
        else:
            print(f"[{iface}] No reply from {target_ip}")

        with lock:
            counter_dict[iface] += 1

    except Exception as e:
        print(f"[{iface}] Ping failed: {e}")
