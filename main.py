import threading
import random
import os
import time
from lib.config_module import parse_config
from lib.ue_generator import generate_ue_profiles
from lib.simulator import Simulator
from lib.logger import setup_logger, set_log_level_by_name

# === Load parsed config ===
cfg = parse_config()

# === Setup logger ===
log_level = getattr(cfg.simulation, 'log_level', 'INFO')
setup_logger(level=log_level)
set_log_level_by_name(log_level)

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

import logging
logger = logging.getLogger("UE-traffic")
logger.info("Simulation started. Waiting for threads to start...")
sim.wait_for_completion()
