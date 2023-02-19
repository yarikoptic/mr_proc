import os
from pathlib import Path
import argparse
import json
import logging
from workflow.dicom_org import run_dicom_org
from workflow.bids_conv import run_bids_conv


# logger
LOG_FILE = "../mr_proc.log"
log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logger = logging.getLogger(__name__)

# To override the default severity of logging
logger.setLevel('INFO')

# Use FileHandler() to log to a file
file_handler = logging.FileHandler(LOG_FILE, mode="w")
formatter = logging.Formatter(log_format)
file_handler.setFormatter(formatter)

# Don't forget to add the file handler
logger.addHandler(file_handler)

# argparse
HELPTEXT = """
Top level script to orchestrate workflows as specified in the global_config.json
"""
parser = argparse.ArgumentParser(description=HELPTEXT)
parser.add_argument('--global_config', type=str, help='path to global config file for your mr_proc dataset')
parser.add_argument('--session_id', type=str, help='current session or visit ID for the dataset')
parser.add_argument('--n_jobs', type=int, default=4, help='number of parallel processes')

args = parser.parse_args()

# read global configs
global_config_file = args.global_config
with open(global_config_file, 'r') as f:
    global_configs = json.load(f)

DATASET_ROOT = global_configs["DATASET_ROOT"]

session_id = args.session_id
n_jobs = args.n_jobs

logger.info("-"*75)
logger.info(f"Starting mr_proc for {DATASET_ROOT} dataset...")
logger.info(f"dataset session (i.e visit): {session_id}")
logger.info(f"Running {n_jobs} in parallel")

workflows = global_configs["WORKFLOWS"]
logger.info(f"Running {workflows} serially")

for wf in workflows:
    logger.info("-"*50)
    logger.info(f"Starting workflow: {wf}")
    if wf == "dicom_org":        
        run_dicom_org.main(global_configs,n_jobs=n_jobs)
    elif wf == "bids_conv": 
        run_bids_conv.main(global_configs, session_id, n_jobs=n_jobs)
    else:
        logger.error(f"Unknown workflow: {wf}")
    logger.info(f"Finishing workflow: {wf}")
    logger.info("-"*50)

logger.info(f"Finishing mr_proc run...")
logger.info("-"*75)