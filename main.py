import threading
import random
import os
import time
import signal
import sys
import argparse
from lib.config_module import parse_config
from lib.ue_generator import generate_ue_profiles
from lib.simulator import Simulator
from lib.logger import setup_logger, set_log_level_by_name

# === Parse command line arguments ===
parser = argparse.ArgumentParser(
    description='UE Traffic Simulator - Simulate network traffic from multiple UEs',
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog='''\nExamples:
  python3 main.py                           # Use default config (config/config.yaml)
  python3 main.py -c myconfig.yaml          # Use custom config file
  python3 main.py --config /path/to/cfg.yaml  # Use config with absolute path
    '''
)
parser.add_argument(
    '-c', '--config',
    type=str,
    default='config/config.yaml',
    help='Path to configuration file (default: config/config.yaml)'
)
args = parser.parse_args()

# === Load parsed config ===
try:
    cfg = parse_config(args.config)
except FileNotFoundError as e:
    print(f"Error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"Error parsing config: {e}")
    sys.exit(1)

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

# === Signal handler for Ctrl+C ===
def signal_handler(sig, frame):
    import logging
    logger = logging.getLogger("UE-traffic")
    print("\n")  # 換行讓輸出更清晰
    logger.warning("Received interrupt signal (Ctrl+C). Stopping simulation...")
    
    # 停止所有線程
    sim.stop_all_threads()
    
    # 顯示最終統計
    print("\n")  # 額外換行
    sim.display.print_final_statistics()
    
    # 保存 CSV
    logger.info("Saving packet records to CSV...")
    sim.recorder.save_csv()
    
    logger.info("Simulation terminated by user.")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

# === Run simulation and display ===

runnung_status = sim.run()             # start all UE threads

if runnung_status == False:
    exit(1)  # exit if validation failed

import logging
logger = logging.getLogger("UE-traffic")
logger.info("Simulation started. Waiting for threads to start...")
sim.wait_for_completion()

# === Normal completion ===
print("\n")  # 換行讓輸出更清晰
sim.display.print_final_statistics()
