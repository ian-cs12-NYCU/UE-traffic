import threading
import random
import os
import time
from config_parser import parse_config
from ue_generator import generate_ue_profiles
from simulator import Simulator

# === Load parsed config ===
cfg = parse_config()
ue_profiles = generate_ue_profiles(cfg.profiles)

# === Create Simulator instance ===
sim = Simulator(
    ue_profiles = ue_profiles,
    duration = cfg.simulation.duration_sec,
    target_ips = cfg.simulation.target_ips,
    packet_type = cfg.simulation.packet_type,
    display_interval = cfg.simulation.display_interval_sec
)

# === Run simulation and display ===

runnung_status = sim.run()             # start all UE threads

if runnung_status == False:
    exit(1)  # exit if validation failed

print("[INFO] Simulation started. Waiting for threads to start...")
sim.wait_for_completion()
