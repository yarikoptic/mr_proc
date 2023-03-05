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
fname = __file__
CWD = os.path.dirname(os.path.abspath(fname))

# logger
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

def run_heudiconv(participant_id, global_configs, session_id, stage, logger):
    logger.info(f"\n***Processing participant: {participant_id}***")
    DATASET_ROOT = global_configs["DATASET_ROOT"]
    DATASTORE_DIR = global_configs["DATASTORE_DIR"]
    SINGULARITY_PATH = global_configs["SINGULARITY_PATH"]
    CONTAINER_STORE = global_configs["CONTAINER_STORE"]
    HEUDICONV_CONTAINER = global_configs["BIDS"]["heudiconv"]["CONTAINER"]
    HEUDICONV_VERSION = global_configs["BIDS"]["heudiconv"]["VERSION"]
    HEUDICONV_CONTAINER = HEUDICONV_CONTAINER.format(HEUDICONV_VERSION)
    SINGULARITY_HEUDICONV = f"{CONTAINER_STORE}/{HEUDICONV_CONTAINER}"

    logger.info(f"Using SINGULARITY_HEUDICONV: {SINGULARITY_HEUDICONV}")

    SINGULARITY_WD = "/scratch"
    SINGULARITY_DICOM_DIR = f"{SINGULARITY_WD}/dicom/ses-{session_id}"
    SINGULARITY_BIDS_DIR = f"{SINGULARITY_WD}/bids"
    SINGULARITY_DATA_STORE="/data"
    HEURISTIC_FILE=f"{SINGULARITY_WD}/proc/heuristic.py"

    # Singularity CMD 
    SINGULARITY_CMD=f"{SINGULARITY_PATH} run -B {DATASET_ROOT}:{SINGULARITY_WD} \
        -B {DATASTORE_DIR}:{SINGULARITY_DATA_STORE} {SINGULARITY_HEUDICONV} "

    # Heudiconv CMD
    subject = "{subject}"
    if stage == 1:
        logger.info("Running stage 1")
        Heudiconv_CMD = f" -d {SINGULARITY_DICOM_DIR}/{subject}/* \
            -s {participant_id} -c none \
            -f convertall \
            -o {SINGULARITY_BIDS_DIR} \
            --overwrite \
            -ss {session_id} "

    elif stage == 2:
        logger.info("Running stage 2")
        Heudiconv_CMD = f" -d {SINGULARITY_DICOM_DIR}/{subject}/* \
            -s {participant_id} -c none \
            -f {HEURISTIC_FILE} \
            --grouping studyUID \
            -c dcm2niix -b --overwrite --minmeta \
            -o {SINGULARITY_BIDS_DIR} \
            -ss {session_id} "

    else:
        logger.error("Incorrect Heudiconv stage: {stage}")

    CMD_ARGS = SINGULARITY_CMD + Heudiconv_CMD 
    CMD = CMD_ARGS.split()

    logger.info(f"CMD:\n{CMD}")
    try:
        heudiconv_proc = subprocess.run(CMD)
    except Exception as e:
        logger.error(f"bids run failed with exceptions: {e}")

def run(global_configs, session_id, stage=2, n_jobs=2):
    """ Runs the bids conv tasks 
    """
    session = f"ses-{session_id}"
    DATASET_ROOT = global_configs["DATASET_ROOT"]
    log_dir = f"{DATASET_ROOT}/scratch/logs/"
    log_file = f"{log_dir}/bids_conv.log"

    logger = get_logger(log_file)
    logger.info("-"*50)
    logger.info(f"Using DATASET_ROOT: {DATASET_ROOT}")
    logger.info(f"Running HeuDiConv stage: {stage}")
    logger.info(f"Number of parallel jobs: {n_jobs}")

    mr_proc_manifest = f"{DATASET_ROOT}/tabular/demographics/mr_proc_manifest.csv"
    dicom_dir = f"{DATASET_ROOT}/dicom/{session}/"
    bids_dir = f"{DATASET_ROOT}/bids/"

    # read current participant manifest 
    manifest_df = pd.read_csv(mr_proc_manifest)

    # filter session
    manifest_df["session_id"] = manifest_df["session_id"].astype(str)
    manifest_df = manifest_df[manifest_df["session_id"] == session_id]
    
    manifest_df["participant_id"] = manifest_df["participant_id"].astype(str)
    participants = manifest_df["participant_id"].str.strip().values
    n_participants = len(participants)

    # generate dicom_id
    manifest_df["dicom_id"] = [''.join(filter(str.isalnum, idx)) for idx in participants]
    dicom_ids = list(manifest_df["dicom_id"])

    # generate bids_id
    manifest_df["bids_id"] = "sub-" + manifest_df["dicom_id"].astype(str)
    bids_ids = list(manifest_df["bids_id"])

    # available participant dicom dirs
    if Path.is_dir(Path(dicom_dir)):
        available_dicom_dirs = next(os.walk(dicom_dir))[1]
    else:
        available_dicom_dirs = []
        logger.warning(f"dicom dirs for {session} does not exist")

    available_dicom_dirs = set(dicom_ids) & set(available_dicom_dirs)
    n_available_dicom_dirs = len(available_dicom_dirs)

    # available participant bids dirs (for particular session)
    current_bids_dirs = next(os.walk(bids_dir))[1]
    current_bids_session_dirs = []
    for pbd in current_bids_dirs:
        ses_dir_path = Path(f"{bids_dir}/{pbd}/{session}")
        if Path.is_dir(ses_dir_path):
            current_bids_session_dirs.append(pbd)

    current_bids_dirs = set(bids_ids) & set(current_bids_session_dirs)
    n_current_bids_dirs = len(current_bids_dirs)

    # check mismatch between manifest and participant dicoms
    missing_dicom_dirs = set(dicom_ids) - set(available_dicom_dirs)
    n_missing_dicom_dirs = len(missing_dicom_dirs)

    current_bids_dirs_dicom_ids = manifest_df[manifest_df["bids_id"].isin(current_bids_dirs)]["dicom_id"]

    # participants to process with Heudiconv
    heudiconv_participants = set(dicom_ids) - set(missing_dicom_dirs) - set(current_bids_dirs_dicom_ids)
    n_heudiconv_participants = len(heudiconv_participants)

    logger.info("-"*50)
    logger.info(f"Identifying participants to be BIDSified\n\n \
    n_particitpants (listed in the mr_proc_manifest): {n_participants}\n \
    n_current_bids_dirs (current): {n_current_bids_dirs}\n \
    n_available_dicom_dirs (available): {n_available_dicom_dirs}\n \
    n_missing_dicom_dirs: {n_missing_dicom_dirs}\n \
    heudiconv participants to processes: {n_heudiconv_participants}\n")
    logger.info("-"*50)

    if n_heudiconv_participants > 0:
        logger.info(f"\nStarting bids conversion for {n_heudiconv_participants} participant(s)")
    
        if stage == 2:
            logger.info(f"Copying ./heuristic.py to {DATASET_ROOT}/proc/heuristic.py (to be seen by Singularity container)")
            shutil.copyfile(f"{CWD}/heuristic.py", f"{DATASET_ROOT}/proc/heuristic.py")

        if n_jobs > 1:
            ## Process in parallel! (Won't write to logs)
            Parallel(n_jobs=n_jobs)(delayed(run_heudiconv)(
                participant_id, global_configs, session_id, stage, logger
                ) for participant_id in heudiconv_participants)

        else:
            # Useful for debugging
            for participant_id in heudiconv_participants:
                run_heudiconv(participant_id, global_configs, session_id, stage, logger) 

        # Check succussful bids
        participant_bids_paths = glob.glob(f"{bids_dir}/sub-*")
        manifest_df.to_csv(mr_proc_manifest,index=None)
        logger.info("-"*50)
        logger.info(f"BIDS conversion completed for the {n_heudiconv_participants} new participants")
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
    parser.add_argument('--stage', type=int, default=2, help='heudiconv stage (either 1 or 2)')
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