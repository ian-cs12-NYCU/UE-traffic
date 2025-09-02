import threading
import random
import os
import time
from config_module import parse_config
from ue_generator import generate_ue_profiles
from simulator import Simulator

# === Load parsed config ===
cfg = parse_config()
ue_profiles = generate_ue_profiles(cfg)

# === Create Simulator instance ===
sim = Simulator(
    ue_profiles = ue_profiles,
    cfg = cfg,
)

# === Run simulation and display ===

runnung_status = sim.run()             # start all UE threads

if runnung_status == False:
    exit(1)  # exit if validation failed

print("[INFO] Simulation started. Waiting for threads to start...")
sim.wait_for_completion()
