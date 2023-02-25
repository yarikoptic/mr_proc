import argparse
import json
import subprocess
import shutil
from pathlib import Path
import pandas as pd
import os
from joblib import Parallel, delayed
import glob
import logging

#Author: nikhil153
#Date: 07-Oct-2022
TEST_RUN="0"
fname = __file__
CWD = os.path.dirname(os.path.abspath(fname))

# logger
def get_logger(log_dir, mode="w", level="DEBUG"):
    """ Initiate a new logger if not provided
    """
    LOG_FILE = f"{log_dir}/dicom_org.log"
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logger = logging.getLogger(__name__)

    logger.setLevel(level)

    file_handler = logging.FileHandler(LOG_FILE, mode=mode)
    formatter = logging.Formatter(log_format)
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)

    return logger

def run_heudiconv(participant_id, global_configs, session_id, stage, logger):
    logger.info(f"\n***Processing participant: {participant_id}***")
    DATASET_ROOT = global_configs["DATASET_ROOT"]
    DATASTORE_DIR = global_configs["DATASTORE_DIR"]
    SINGULARITY_PATH = global_configs["SINGULARITY_PATH"]
    CONTAINER_STORE = global_configs["CONTAINER_STORE"]
    HEUDICONV_CONTAINER = global_configs["BIDS"]["heudiconv"]["CONTAINER"]
    HEUDICONV_VERSION = global_configs["BIDS"]["heudiconv"]["VERSION"]
    HEUDICONV_CONTAINER = HEUDICONV_CONTAINER.format(HEUDICONV_VERSION)
    SINGULARITY_HEUDICONV = f"{CONTAINER_STORE}{HEUDICONV_CONTAINER}"
    logger.info(f"Using SINGULARITY_HEUDICONV: {SINGULARITY_HEUDICONV}")
    
    # Run HeuDiConv script
    HEUDICONV_SCRIPT = f"{CWD}/scripts/heudiconv_stage_{stage}.sh"
    HEUDICONV_ARGS = ["-d", DATASET_ROOT, "-i", SINGULARITY_HEUDICONV, "-r", SINGULARITY_PATH, \
                    "-p", participant_id, "-s", session_id, "-l", DATASTORE_DIR, "-t", TEST_RUN]
    HEUDICONV_CMD = [HEUDICONV_SCRIPT] + HEUDICONV_ARGS

    try:
        heudiconv_proc = subprocess.run(HEUDICONV_CMD)
    except Exception as e:
        logger.error(f"bids run failed with exceptions: {e}")

def run(global_configs, session_id, stage=2, n_jobs=2):

    DATASET_ROOT = global_configs["DATASET_ROOT"]
    log_dir = f"{DATASET_ROOT}/scratch/logs/"
    log_file = f"{log_dir}/bids_conv.log"

    logger = get_logger(log_file)
    logger.info("-"*50)
    logger.info(f"Using DATASET_ROOT: {DATASET_ROOT}")
    logger.info(f"Running HeuDiConv stage: {stage}")
    logger.info(f"Number of parallel jobs: {n_jobs}")

    mr_proc_manifest = f"{DATASET_ROOT}/tabular/demographics/mr_proc_manifest.csv"
    dicom_dir = f"{DATASET_ROOT}dicom/"
    bids_dir = f"{DATASET_ROOT}bids/"

    # read current participant manifest 
    manifest_df = pd.read_csv(mr_proc_manifest)
    participants = manifest_df["participant_id"].str.strip().values
    n_participants = len(participants)

    # generate bids_id
    manifest_df["dicom_id"] = [''.join(filter(str.isalnum, idx)) for idx in participants]
    manifest_df["bids_id"] = "sub-" + manifest_df["dicom_id"].astype(str)
    dicom_ids = list(manifest_df["dicom_id"])
    bids_ids = list(manifest_df["bids_id"])

    # available participant dicom dirs
    participant_dicom_dirs = next(os.walk(dicom_dir))[1]
    participant_dicom_dirs = set(dicom_ids) & set(participant_dicom_dirs)
    n_participant_dicom_dirs = len(participant_dicom_dirs)

    # available participant bids dirs
    participant_bids_dirs = next(os.walk(bids_dir))[1]
    participant_bids_dirs = set(bids_ids) & set(participant_bids_dirs)
    n_participant_bids_dirs = len(participant_bids_dirs)

    # check mismatch between manifest and participant dicoms
    missing_dicom_dirs = set(dicom_ids) - set(participant_dicom_dirs)
    n_missing_dicom_dirs = len(missing_dicom_dirs)

    participant_bids_dirs_dicom_ids = manifest_df[manifest_df["bids_id"].isin(participant_bids_dirs)]["dicom_id"]

    # participants to process with Heudiconv
    heudiconv_participants = set(dicom_ids) - set(missing_dicom_dirs) - set(participant_bids_dirs_dicom_ids)
    n_heudiconv_participants = len(heudiconv_participants)

    logger.info("-"*50)
    logger.info("Identifying participants to be BIDSified\n"
    f"  n_particitpants: {n_participants}\n \
    n_participant_bids_dirs: {n_participant_bids_dirs}\n \
    n_participant_dicom_dirs: {n_participant_dicom_dirs}\n \
    n_missing_dicom_dirs: {n_missing_dicom_dirs}\n \
    heudiconv participants to processes: {n_heudiconv_participants}")
    logger.info("-"*50)

    if n_heudiconv_participants > 0:
        # Copy heuristic.py into "DATASET_ROOT/proc/heuristic.py"
        if stage == 2:
            logger.info(f"Copying ./heuristic.py to {DATASET_ROOT}/proc/heuristic.py (to be seen by Singularity container)")
            shutil.copyfile(f"{CWD}/heuristic.py", f"{DATASET_ROOT}/proc/heuristic.py")

        ## Process in parallel! 
        Parallel(n_jobs=n_jobs)(delayed(run_heudiconv)(participant_id, global_configs, session_id, stage) for participant_id in heudiconv_participants)

        # Check succussful bids
        participant_bids_paths = glob.glob(f"{bids_dir}/sub-*")
        manifest_df.to_csv(mr_proc_manifest,index=None)
        logger.info("-"*50)
        logger.info(f"BIDS conversion completed for the new {n_heudiconv_participants} participants")
        logger.info(f"Current successfully converted BIDS participants: {len(participant_bids_paths)}")
        
    else:
        logger.info(f"No new participants found for bids conversion...")

    logger.info("-"*50)
    logger.info("")

if __name__ == '__main__':
    # argparse
    HELPTEXT = """
    Script to perform DICOM to BIDS conversion using HeuDiConv
    """
    parser = argparse.ArgumentParser(description=HELPTEXT)

    parser.add_argument('--global_config', type=str, help='path to global configs for a given mr_proc dataset')
    parser.add_argument('--session_id', type=str, help='session id for the participant')
    parser.add_argument('--stage', type=int, help='heudiconv stage (either 1 or 2)')
    parser.add_argument('--n_jobs', type=int, default=2, help='number of parallel processes')

    args = parser.parse_args()

    global_config_file = args.global_config
    session_id = args.session_id
    stage = args.stage
    n_jobs = args.n_jobs

    # Read global configs
    with open(global_config_file, 'r') as f:
        global_configs = json.load(f)

    run(global_configs, session_id, stage, n_jobs)