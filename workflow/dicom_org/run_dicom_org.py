import pandas as pd
import numpy as np
import glob
import os
from pathlib import Path
import argparse
import json
import logging
from workflow.dicom_org.utils import search_dicoms, copy_dicoms
from joblib import Parallel, delayed

#Author: nikhil153
#Date: 07-Oct-2022

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

def reorg(participant, raw_dicom_dir, dicom_dir, log_dir, logger, use_symlinks=True):
    """ Copy / Symlink raw dicoms into a flat participant dir
    """
    logger.info(f"\nparticipant_id: {participant}")
    # print(f"\nparticipant_id: {participant}")

    participant_raw_dicom_dir = f"{raw_dicom_dir}/{participant}/"
    # print(f"participant_dir: {participant_raw_dicom_dir}")
    raw_dcm_list, invalid_dicom_list = search_dicoms(participant_raw_dicom_dir)
    logger.info(f"n_raw_dicom: {len(raw_dcm_list)}, n_skipped (invalid/derived): {len(invalid_dicom_list)}")
    # print(f"n_raw_dicom: {len(raw_dcm_list)}, n_skipped (invalid/derived): {len(invalid_dicom_list)}")

    # Remove non-alphanumeric chars (e.g. "_" from the participant_dir names)
    bids_participant = ''.join(filter(str.isalnum, participant))
    participant_dicom_dir = f"{dicom_dir}{bids_participant}/"
    
    copy_dicoms(raw_dcm_list, participant_dicom_dir, use_symlinks)
    
    # Log skipped invalid dicom list for the participant
    invalid_dicoms_file = f"{log_dir}{participant}_invalid_dicoms.json"
    invalid_dicom_dict = {participant: invalid_dicom_list}
    # Save skipped or invalid dicom file list
    with open(invalid_dicoms_file, "w") as outfile:
        json.dump(invalid_dicom_dict, outfile, indent=4)
        

def main(global_configs, session, use_symlinks, n_jobs):
    # populate relative paths
    DATASET_ROOT = global_configs["DATASET_ROOT"]
    raw_dicom_dir = f"{DATASET_ROOT}/scratch/raw_dicom/{session}/"
    dicom_dir = f"{DATASET_ROOT}/dicom/{session}/"
    log_dir = f"{DATASET_ROOT}/scratch/logs/"
    mr_proc_manifest = f"{DATASET_ROOT}/tabular/demographics/mr_proc_manifest.csv"

    logger = get_logger(log_dir)
    logger.info("-"*50)
    logger.info(f"Using DATASET_ROOT: {DATASET_ROOT}")
    logger.info(f"symlinks: {use_symlinks}")
    logger.info(f"Number of parallel jobs: {n_jobs}")

    # read current participant manifest 
    manifest_df = pd.read_csv(mr_proc_manifest)
    participants = manifest_df["participant_id"].astype(str).str.strip().values
    manifest_df["dicom_ids"] = [''.join(filter(str.isalnum, idx)) for idx in participants]
    dicom_ids = manifest_df["dicom_ids"]

    n_participants = len(participants)

    # check current dicom dir
    current_dicom_dirs = next(os.walk(dicom_dir))[1]
    n_participant_dicom_dirs = len(current_dicom_dirs)
    current_dicom_dirs_participant_ids = manifest_df[manifest_df["dicom_ids"].isin(current_dicom_dirs)]["participant_id"]

    # check raw dicom dir
    available_dicom_dirs = next(os.walk(raw_dicom_dir))[1]
    n_available_dicom_dirs = len(available_dicom_dirs)

    # check mismatch between manifest and raw_dicoms
    missing_dicom_dirs = set(participants) - set(available_dicom_dirs)
    n_missing_dicom_dirs = len(missing_dicom_dirs)

    # identify participants to be reorganized 
    dicom_reorg_participants = set(participants) - set(current_dicom_dirs_participant_ids) - missing_dicom_dirs
    n_dicom_reorg_participants = len(dicom_reorg_participants)

    print("-"*50)
    print("Identifying participants to be reorganized\n"
    f"  n_particitpants: {n_participants}\n \
    n_particitpant_dicom_dirs: {n_participant_dicom_dirs}\n \
    n_available_dicom_dirs: {n_available_dicom_dirs}\n \
    n_missing_dicom_dirs: {n_missing_dicom_dirs}\n \
    dicom_reorg_participants: {n_dicom_reorg_participants}")

    logger.info("-"*50)
    logger.info("Identifying participants to be reorganized\n"
    f"  n_particitpants: {n_participants}\n \
    n_particitpant_dicom_dirs: {n_participant_dicom_dirs}\n \
    n_available_dicom_dirs: {n_available_dicom_dirs}\n \
    n_missing_dicom_dirs: {n_missing_dicom_dirs}\n \
    dicom_reorg_participants: {n_dicom_reorg_participants}")

    # start reorganizing
    if n_dicom_reorg_participants > 0:
        Path(f"{log_dir}").mkdir(parents=True, exist_ok=True)

        ## Process in parallel! 
        logger.info(f"\nStarting dicom reorg for {n_dicom_reorg_participants} participant(s)")
        Parallel(n_jobs=n_jobs)(delayed(reorg)(participant_id, raw_dicom_dir, dicom_dir, log_dir, logger, use_symlinks) for participant_id in dicom_reorg_participants)

        print(f"\nDICOM reorg for {n_dicom_reorg_participants} participants completed")
        print(f"Skipped (invalid/derived) DICOMs are listed here: {log_dir}")
        print(f"DICOMs are now copied into {dicom_dir} and ready for bids conversion!")
        logger.info(f"\nDICOM reorg for {n_dicom_reorg_participants} participants completed")
        logger.info(f"Skipped (invalid/derived) DICOMs are listed here: {log_dir}")
        logger.info(f"DICOMs are now copied into {dicom_dir} and ready for bids conversion!")

    else:
        print(f"No new participants found for dicom reorg...")
        logger.info(f"No new participants found for dicom reorg...")

    print("-"*50)
    print("")


if __name__ == '__main__':
    # argparse
    HELPTEXT = """
    Script to reorganize raw (scanner dump) DICOMs into flatterned dir structure needed for BIDS conversion using HeuDiConv
    """
    parser = argparse.ArgumentParser(description=HELPTEXT)
    parser.add_argument('--global_config', type=str, help='path to global config file for your mr_proc dataset')
    parser.add_argument('--session_id', type=str, default=None, help='session (i.e. visit to process)')
    parser.add_argument('--use_symlinks', action='store_true', help='symlink from raw_dicom to dicom to avoid duplication')
    parser.add_argument('--n_jobs', type=int, default=4, help='number of parallel processes')
    args = parser.parse_args()

    # read global configs
    global_config_file = args.global_config
    with open(global_config_file, 'r') as f:
        global_configs = json.load(f)

    session_id = args.session_id
    session = f"ses-{session_id}"
    use_symlinks = args.use_symlinks # Saves space and time! 
    n_jobs = args.n_jobs

    main(global_configs, session, use_symlinks, n_jobs)