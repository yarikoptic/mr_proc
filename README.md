# mr_proc 
A workflow for standarized MR images processing. 
*Process long and prosper.*

## Documentation

### mr_proc modules

- [mr_proc](https://www.neurobagel.org/documentation/mr_proc/overview/)

---

## Quickstart (How to run a preset workflow setup)
### Onetime setup
1. Project
   - Create a project dir on your local machine: `mkdir /home/<user>/projects/<my_project>`
   - Create `containers`, `code`, `data`  dirs inside your project dir.  
2. Containers (Singulaity)
   - Install [Singularity](https://singularity-tutorial.github.io/01-installation/)
   - Download containers (e.g. Heudiconv) for the pipelines used in this workflow inside the `containers` dir. 
3. Code
   - Change dir to `code`: `cd /home/<user>/projects/<my_project>/code/`
   - Create a new [venv](https://realpython.com/python-virtual-environments-a-primer/): `python3 -m venv mr_proc_env` 
   - Activate your env: `source mr_proc_env/bin/activate` 
   - Clone this repo: `git clone https://github.com/neurodatascience/mr_proc.git`
   - Change dir to `mr_proc` and checkout nimhans branch: `git checkout nimhans` 
   - Install python dependencies: `pip install -e .`  
4. Data 
   - Change dir to mr_proc scripts: `cd /home/<user>/projects/<my_project>/code/mr_proc/scripts`
   - Create mr_proc dataset-tree: `./mr_proc_setup.sh /home/<user>/projects/<my_project>/data <study_name>`
   - Create and populate `<study_name>/tabular/global_configs.json` 
   - Copy your participant-level dicom dirs (e.g. `MNI001`, `MNI002` ...) into `<study_name>/scratch/raw_dicom/`
   
### Periodic runs
1. Update the `mr_proc_manifest.csv` in `/home/<user>/projects/<my_project>/data/<study_name>/tabular/demographics` comprising at least `participant_id`,`age`,`sex`,`group` (typically a diagnosis) columns.   
2. Change dir to `code`: `cd /home/<user>/projects/<my_project>/code/`
2. Activate your env: `source mr_proc/bin/activate` (if starting with a new terminal)
3. Change dir to mr_proc scripts: `cd /home/<user>/projects/<my_project>/code/mr_proc/scripts`
4. Run mr_proc: `python run_mr_proc.py --global_config <> --session_id <> --n_jobs <>`

### Expected output
1. `<study_name>/dicom`: Participant-level dirs with symlinks to the dicom files in the raw_dicom dir
   - Note: dicoms that are unreadable or contain derived (i.e. scanner processed) scans will be skipped and enlisted in the `<study_name>/scratch/logs`
2. `<study_name>/bids`: BIDS dataset comprising all the modalities in Nifti format (i.e. nii.gz and sidecar json)

---

### Individual containerized pipelines:

- [Heudionv](https://heudiconv.readthedocs.io/en/latest/installation.html#singularity) 
- [MRIQC](https://mriqc.readthedocs.io/en/stable/)
- [fMRIPrep](https://fmriprep.org/en/1.5.5/singularity.html) 
- [TractoFlow](https://github.com/scilus/tractoflow)
- [MAGeT Brain](https://github.com/CoBrALab/MAGeTbrain)

