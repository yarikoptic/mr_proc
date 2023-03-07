# mr_proc (QPN)
A workflow for standarized MR images processing. 
*Process long and prosper.*

## Documentation

### mr_proc modules

- [mr_proc](https://www.neurobagel.org/documentation/mr_proc/overview/)

### Individual containerized pipelines:

- [Heudionv](https://heudiconv.readthedocs.io/en/latest/installation.html#singularity) 
- [MRIQC](https://mriqc.readthedocs.io/en/stable/)
- [fMRIPrep](https://fmriprep.org/en/1.5.5/singularity.html) 
- [TractoFlow](https://github.com/scilus/tractoflow)
- [MAGeT Brain](https://github.com/CoBrALab/MAGeTbrain)

--- 

## QPN notes

### Recruitment (imaging) and participant naming
- Recruitment updates are provided by study coordinator(s) in a Google Sheet: `QPN_Imaging_Codes.xlsx`.
- Latest LORIS participant manifest is fetched from [LORIS](https://copn.loris.ca/). 
  
### MRI acquition
#### Available modalities and protocols
![QPN MR acq protocols](./images/QPN_dicom_protocols.png)

### Clinical data
- TODO

### Containers used (Singularity)
- [Heudionv](https://heudiconv.readthedocs.io/en/latest/installation.html#singularity) (current version: `0.11.6`)
- [BIDS validator](https://github.com/bids-standard/bids-validator)
- [fMRIPrep](https://fmriprep.org/en/1.5.5/singularity.html) (current version: `20.2.7`)

### Issues

- Filenames mismatch between Heudiconv and [BIDS BEP](https://github.com/bids-standard/bep001/blob/master/src/04-modality-specific-files/01-magnetic-resonance-imaging-data.md). Use modify [fix_heudiconv_naming.sh](bids/scripts/fix_heudiconv_naming.sh) to fix issues.
- Heudiconv will generate two NIFTIs with PDT2 suffix with different echo index - which may not be ideal for certain pipelines which require separate PDw and T2w suffixes. 
- ~~Heudiconv will also swap the order of "echo" and "part" for MEGRE scans.~~ (This has been fixed in the Heudiconv `v0.11.6`, which now used as a container for this processing)
- Heudiconv adds mysterious suffix - possibly due to how dcm2nix handles multi-echo conversion see [neurostar issue](https://neurostars.org/t/heudiconv-adding-unspecified-suffix/21450/3) 
- Examples: 1) sub-PD00509D598628_ses-01_run-3_T1w_heudiconv822a_ROI1.nii.gz 2) sub-PD00509D598628_ses-01_run-3_T1w2.nii.gz
- Currently removing these files manually since only 3 subjects have this issue: PD00119D567297, PD00509D598628, PD00435D874573
