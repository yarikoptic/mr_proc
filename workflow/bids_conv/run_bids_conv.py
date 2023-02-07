import argparse
import json
import subprocess
import shutil
from pathlib import Path
import pandas as pd
import os
from joblib import Parallel, delayed

#Author: nikhil153
#Date: 07-Oct-2022


def run_heudiconv(participant_id):
    print(f"\n***Processing participant: {participant_id}***")
    participant_subdir_path = f"{DATASET_ROOT}/dicom/{participant_id}"

    # Run HeuDiConv script
    HEUDICONV_SCRIPT = f"scripts/heudiconv_stage_{stage}.sh"
    HEUDICONV_ARGS = ["-d", DATASET_ROOT, "-i", SINGULARITY_HEUDICONV, "-r", SINGULARITY_PATH, \
                    "-p", participant_id, "-s", session_id, "-l", DATASTORE_DIR, "-t", test_run]
    HEUDICONV_CMD = [HEUDICONV_SCRIPT] + HEUDICONV_ARGS

    try:
        heudiconv_proc = subprocess.run(HEUDICONV_CMD)
    except Exception as e:
        print(f"bids run failed with exceptions: {e}")

# argparse
HELPTEXT = """
Script to perform DICOM to BIDS conversion using HeuDiConv
"""
parser = argparse.ArgumentParser(description=HELPTEXT)

parser.add_argument('--global_config', type=str, help='path to global configs for a given mr_proc dataset')
parser.add_argument('--session_id', type=str, help='session id for the participant')
parser.add_argument('--stage', type=int, help='heudiconv stage (either 1 or 2)')
parser.add_argument('--n_jobs', type=int, default=4, help='number of parallel processes')


args = parser.parse_args()

global_config_file = args.global_config
session_id = args.session_id
stage = args.stage
n_jobs = args.n_jobs
test_run = "0"

# Read global configs
with open(global_config_file, 'r') as f:
    global_configs = json.load(f)

DATASET_ROOT = global_configs["DATASET_ROOT"]
DATASTORE_DIR = global_configs["DATASTORE_DIR"]
SINGULARITY_PATH = global_configs["SINGULARITY_PATH"]
CONTAINER_STORE = global_configs["CONTAINER_STORE"]

HEUDICONV_CONTAINER = global_configs["BIDS"]["heudiconv"]["CONTAINER"]
HEUDICONV_VERSION = global_configs["BIDS"]["heudiconv"]["VERSION"]
HEUDICONV_CONTAINER = HEUDICONV_CONTAINER.format(HEUDICONV_VERSION)

SINGULARITY_HEUDICONV = f"{CONTAINER_STORE}{HEUDICONV_CONTAINER}"

print("--------------------------------------------------------------------------")
print(f"Using DATASET_ROOT: {DATASET_ROOT}")
print(f"Using SINGULARITY_HEUDICONV: {SINGULARITY_HEUDICONV}")
print(f"Running HeuDiConv stage: {stage}")
print(f"Number of parallel jobs: {n_jobs}")

mr_proc_manifest = f"{DATASET_ROOT}/tabular/demographics/mr_proc_manifest.csv"
dicom_dir = f"{DATASET_ROOT}dicom/"
bids_dir = f"{DATASET_ROOT}bids/"

# read current participant manifest 
manifest_df = pd.read_csv(mr_proc_manifest)
participants = manifest_df["participant_id"].str.strip().values
n_participants = len(participants)

# available participant dicom dirs
participant_dicom_dirs = next(os.walk(dicom_dir))[1]
n_participant_dicom_dirs = len(set(participants) & set(participant_dicom_dirs))

# available participant bids dirs
participant_bids_dirs = next(os.walk(bids_dir))[1]
n_participant_bids_dirs = len(set(participants) & set(participant_bids_dirs))

# check mismatch between manifest and participant dicoms
missing_dicom_dirs = set(participants) - set(participant_dicom_dirs)
n_missing_dicom_dirs = len(missing_dicom_dirs)

# participants to process with Heudiconv
heudiconv_participants = set(participants) - set(participant_bids_dirs) - missing_dicom_dirs
n_heudiconv_participants = len(heudiconv_participants)
print("--------------------------------------------------------------------------")
print("Identifying participants to be BIDSified\n"
f" n_particitpants: {n_participants}\n \
n_participant_bids_dirs: {n_participant_bids_dirs}\n \
n_participant_dicom_dirs: {n_participant_dicom_dirs}\n \
n_missing_dicom_dirs: {n_missing_dicom_dirs}\n \
heudiconv participants to processes: {n_heudiconv_participants}")
print("--------------------------------------------------------------------------")

# Copy heuristic.py into "DATASET_ROOT/proc/heuristic.py"
if stage == 2:
    print(f"Copying ./heuristic.py to {DATASET_ROOT}/proc/heuristic.py (to be seen by Singularity container)")
    shutil.copyfile("heuristic.py", f"{DATASET_ROOT}/proc/heuristic.py")

Parallel(n_jobs=n_jobs)(delayed(run_heudiconv)(participant_id) for participant_id in heudiconv_participants)
