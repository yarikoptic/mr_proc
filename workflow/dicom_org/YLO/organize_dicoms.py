import pandas as pd
import numpy as np
import glob
import os
from pathlib import Path
import shutil
import argparse
import json
from utils import search_dicoms, copy_dicoms

HELPTEXT = """
Script to reorganize raw (scanner dump) DICOMs into flatterned dir structure needed for BIDS conversion using HeuDiConv
"""
#Author: nikhil153
#Date: 07-Oct-2022

# argparse
parser = argparse.ArgumentParser(description=HELPTEXT)
parser.add_argument('--global_config', type=str, help='path to global config file for your mr_proc dataset')
args = parser.parse_args()

# read global configs
global_config_file = args.global_config

with open(global_config_file, 'r') as f:
    global_configs = json.load(f)

# populate relative paths
dataset_root = global_configs["DATASET_ROOT"]
raw_dicom_dir = f"{dataset_root}scratch/raw_dicom/"
dicom_dir = f"{dataset_root}dicom/"
mr_proc_manifest = f"{dataset_root}/tabular/demographics/mr_proc_manifest.csv"

# read current participant manifest 
manifest_df = pd.read_csv(mr_proc_manifest)
participants = manifest_df["participant_id"].str.strip().values
n_participants = len(participants)

# check current dicom dir
participant_dicom_dirs = os.listdir(f"{dataset_root}/dicom/")
n_participant_dicom_dirs = len(participant_dicom_dirs)

# identify participants to be reorganized 
dicom_reorg_participants = set(participants) - set(participant_dicom_dirs)
n_dicom_reorg_participants = len(dicom_reorg_participants)

print("--------------------------------------------------------------------------")
print("Identifying participants to be reorganized")
print(f"n_particitpants: {n_participants} \
    n_particitpant_dicom_dirs: {n_participant_dicom_dirs} \
    dicom_reorg_participants: {n_dicom_reorg_participants}")

# start reorganizing
if n_dicom_reorg_participants > 0:

    invalid_dicom_list_file = f"{raw_dicom_dir}invalid_dicom_list.json"
    if Path(invalid_dicom_list_file).is_file():
        with open(invalid_dicom_list_file, 'r') as f:
            invalid_dicom_dict = json.load(f)
    else:
        invalid_dicom_dict = {}
        
    print(f"\nStarting dicom reorg for {n_dicom_reorg_participants} participant(s)")
    for participant in dicom_reorg_participants:
        print(f"\nparticipant_id: {participant}")
        participant_raw_dicom_dir = f"{raw_dicom_dir}{participant}/"
        raw_dcm_list, invalid_dicom_list = search_dicoms(participant_raw_dicom_dir)
        print(f"n_raw_dicom: {len(raw_dcm_list)}, n_skipped (invalid/derived): {len(invalid_dicom_list)}")
        participant_dicom_dir = f"{dicom_dir}{participant}/"
        copy_dicoms(raw_dcm_list, participant_dicom_dir)

        invalid_dicom_dict[participant] = invalid_dicom_list

    # Save skipped or invalid dicom file list
    with open(invalid_dicom_list_file, "a") as outfile:
        json.dump(invalid_dicom_dict, outfile)

    print(f"\nDICOM reorg for {n_dicom_reorg_participants} participants completed")
    print(f"Skipped (invalid/derived) DICOMs are listed here: {dicom_dir}invalid_dicom_list_file")
    print(f"DICOMs are now copied into {dicom_dir} and ready for bids conversion!")

else:
    print(f"No new participants found for dicom reorg...")

print("--------------------------------------------------------------------------\n")