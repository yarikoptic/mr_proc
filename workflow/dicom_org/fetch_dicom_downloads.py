import pandas as pd
import numpy as np
import glob
import os
from pathlib import Path
import argparse
import json
import logging
import subprocess
from workflow.dicom_org.utils import search_dicoms, copy_dicoms
from joblib import Parallel, delayed
import workflow.catalog as catalog

#Author: nikhil153
#Date: 07-Oct-2022

fname = __file__
CWD = os.path.dirname(os.path.abspath(fname))
FETCH_SCRIPT = f"{CWD}/scripts/fetch_new_scans.sh"

def get_logger(log_file, mode="w", level="DEBUG"):
    """ Initiate a new logger if not provided
    """
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logger = logging.getLogger(__name__)

    logger.setLevel(level)

    file_handler = logging.FileHandler(log_file, mode=mode)
    formatter = logging.Formatter(log_format)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # output to terminal as well
    stream = logging.StreamHandler()
    streamformat = logging.Formatter(log_format)
    stream.setFormatter(streamformat)
    logger.addHandler(stream)
    
    return logger

def run(global_configs, session_id, n_jobs):
    """ Runs the dicom fetch 
    """
    
    session = f"ses-{session_id}"

    # populate relative paths
    DATASET_ROOT = global_configs["DATASET_ROOT"]
    raw_dicom_dir = f"{DATASET_ROOT}/scratch/raw_dicom/{session}/"
    log_dir = f"{DATASET_ROOT}/scratch/logs/"
    log_file = f"{log_dir}/dicom_fetch.log"

    mr_proc_manifest = f"{DATASET_ROOT}/tabular/demographics/mr_proc_manifest.csv"
    
    logger = get_logger(log_file)
    logger.info("-"*50)
    logger.info(f"Using DATASET_ROOT: {DATASET_ROOT}")
    logger.info(f"symlinks: {use_symlinks}")
    logger.info(f"session: {session}")
    logger.info(f"Number of parallel jobs: {n_jobs}")

    download_df = catalog.get_new_downloads(mr_proc_manifest, raw_dicom_dir, session_id, logger)
    download_participants = download_df["participant_id"].values
    n_download_participants = len(download_participants)
    if n_download_participants > 0:
        for participant_id in download_participants:            
            ARGS = [raw_dicom_dir, participant_id, log_file]
            CMD = [FETCH_SCRIPT] + ARGS
            fetch_proc = subprocess.run(CMD)
        
        logger.info(f"Downloaded DICOMs are now copied into {raw_dicom_dir} and ready for dicom_reorg!")
    else:
        logger.info(f"No new participants found for dicom fetch...")
    

if __name__ == '__main__':
    # argparse
    HELPTEXT = """
    Script to copy dicom dumps into mr_proc scratch/raw_dicom dir
    """
    parser = argparse.ArgumentParser(description=HELPTEXT)
    parser.add_argument('--global_config', type=str, help='path to global config file for your mr_proc dataset')
    parser.add_argument('--session_id', type=str, default=None, help='session (i.e. visit to process)')
    parser.add_argument('--n_jobs', type=int, default=4, help='number of parallel processes')
    args = parser.parse_args()

    # read global configs
    global_config_file = args.global_config
    with open(global_config_file, 'r') as f:
        global_configs = json.load(f)

    session_id = args.session_id
    use_symlinks = args.use_symlinks # Saves space and time! 
    n_jobs = args.n_jobs

    run(global_configs, session_id, n_jobs)