import os
# Heuristics created by nikhil153 (GH) for QPN data.
# 10 Jan 2022

POPULATE_INTENDED_FOR_OPTS = {
        'matching_parameters': ['ModalityAcquisitionLabel'],
        'criterion': 'Closest'
}

def create_key(template, outtype=('nii.gz',), annotation_classes=None):
    if template is None or not template:
        raise ValueError('Template must be a valid format string')
    return template, outtype, annotation_classes

def infotodict(seqinfo):
    """Heuristic evaluator for determining which runs belong where
    allowed template fields - follow python string module:
    item: index within category
    subject: participant id
    seqitem: run number during scanning
    subindex: sub index within group
    """


    #---------anat-----------#
    T1w = create_key('sub-{subject}/{session}/anat/sub-{subject}_{session}_run-{item:01d}_T1w')
    
    # Suffix PDT2 or MESET2 failed BIDS validation
    # Recommendation is to use MESE: https://github.com/bids-standard/bids-specification/issues/223
    # If your image proc pipeline expects T2w suffix, run the "fix_heudiconv_naming.sh" to rename these files" 
    PDT2 = create_key('sub-{subject}/{session}/anat/sub-{subject}_{session}_run-{item:01d}_MESE') #Proton Density (short TE), and #T2 (long TE)

    T2starMag = create_key('sub-{subject}/{session}/anat/sub-{subject}_{session}_run-{item:01d}_part-mag_T2starw')
    T2starPhase = create_key('sub-{subject}/{session}/anat/sub-{subject}_{session}_run-{item:01d}_part-phase_T2starw')
    
    T1wNeuromel = create_key('sub-{subject}/{session}/anat/sub-{subject}_{session}_acq-NM_run-{item:01d}_T1w')
    
    # This needs to have specific order: https://neurostars.org/t/multi-echo-anatomical-mri-bids-questions/17157/16
    # sub-01_run-1_dir-AP_echo-1_part-mag_MEGRE.nii.gz # QPN doesn't have "dir for MEGRE"
    # sub-01_run-1_dir-AP_echo-1_part-phase_MEGRE.nii.gz
    # However, current Heudiconv swaps the order of "echo" and "part" casing BIDS validator to fail. 
    # Additional script ("fix_heudiconv_naming.sh" is created to rename these post hoc.)
    MEGREMag = create_key('sub-{subject}/{session}/anat/sub-{subject}_{session}_run-{item:01d}_part-mag_MEGRE')
    MEGREPhase = create_key('sub-{subject}/{session}/anat/sub-{subject}_{session}_run-{item:01d}_part-phase_MEGRE')
    
    FLAIR = create_key('sub-{subject}/{session}/anat/sub-{subject}_{session}_run-{item:01d}_FLAIR')
    
    # Not sure how to classify this under BIDS (see gen_heuristics for TE/TR detail)
    # Only one subject has this acq
    # TRUFISP = create_key('sub-{subject}/{session}/anat/sub-{subject}_{session}_run-{item:01d}_acq-TRUFISP_T2')

    #---------dwi-----------#
    dwi = create_key('sub-{subject}/{session}/dwi/sub-{subject}_{session}_run-{item:01d}_dwi')
    dwiAP = create_key('sub-{subject}/{session}/dwi/sub-{subject}_{session}_dir-AP_run-{item:01d}_dwi')
    dwiPA = create_key('sub-{subject}/{session}/dwi/sub-{subject}_{session}_dir-PA_run-{item:01d}_dwi')
    
    #---------func-----------#
    bold = create_key('sub-{subject}/{session}/func/sub-{subject}_{session}_task-rest_run-{item:01d}_bold')

    #---------fmap-----------#
    boldGREfmapMag = create_key('sub-{subject}/{session}/fmap/sub-{subject}_{session}_acq-bold_run-{item:01d}_magnitude')
    boldGREfmapPhase = create_key('sub-{subject}/{session}/fmap/sub-{subject}_{session}_acq-bold_run-{item:01d}_phasediff')

    epiAP = create_key('sub-{subject}/{session}/fmap/sub-{subject}_{session}_acq-bold_dir-AP_run-{item:01d}_epi')
    epiPA = create_key('sub-{subject}/{session}/fmap/sub-{subject}_{session}_acq-bold_dir-PA_run-{item:01d}_epi')

    # info dict to be populated
    info = {T1w: [], PDT2: [], T2starMag: [], T2starPhase: [], MEGREMag: [], MEGREPhase: [], T1wNeuromel: [], FLAIR: [], dwi: [], 
            dwiAP: [], dwiPA: [], bold: [], boldGREfmapMag: [], boldGREfmapPhase:[], epiAP: [], epiPA: []
           }
    
    # This is based on heudiconv run_1 output file:dicominfo.tsv from all subjects
    keys_protocols_dict = {
        T1w:['MPRAGE_iPAT2','3DT1','3DT1_Repeat'],
        PDT2: ['PD T2 1sequence','PD_T2','PD_T2_Repeat','PD_T2_Repeat2'],
        "T2star":['AXIAL_T2_STAR_iPAT2','T2-star','T2-star_Repeat'], # # need to check mag vs phase from image_type #GRE classification based on QPN_MR.xlsx
        "MEGRE": ['GRE_10_echos_Dr Collins','GRE_10_echos_Dr Collins_Repeat'], # need to check mag vs phase from image_type
        FLAIR:['Axial T2-FLAIR_iPAT2','2D_FLAIR_FS','2D_FLAIR_FS_Repeat','2D_FLAIR_FS_repeat'],
        # TRUFISP: ['SAG TRUFISP'], #Not sure how to classify this under BIDS (see gen_heuristics for TE/TR detail)
        T1wNeuromel:['T1W Neuromel_TR600_1.8mm_TE10_FA120_BW180_7av'],
        dwi:['DWI','DTI-EDM'],
        dwiAP: ['DTI-B03_AP','DWI-B02_AP'], # only PD00760 has DWI_B02_AP in dicoms and not in QPN loris
        dwiPA: ['DTI-B03_PA','DWI-B03_PA'], # only PD00760 has DWI_B03_AP in dicoms and not in QPN loris
        bold:['BOLD Resting State AC-PC','RS-fMRI'],        
        "boldGREfmap":['BOLD_RS_gre_field_mapping'], # need to check mag vs phase from image_type
        epiAP:['RS_fMRI_se_AP'],
        epiPA:['RS_fMRI_se_PA']
    }

    protocols_with_mag_and_phase = {
                                    "T2star":[T2starMag,T2starPhase],
                                    "MEGRE": [MEGREMag,MEGREPhase],
                                    "boldGREfmap": [boldGREfmapMag, boldGREfmapPhase]
                                    }

    data = create_key('run{item:03d}')
    last_run = len(seqinfo)
    for idx, s in enumerate(seqinfo):
        print(s)
        for key,protocols in keys_protocols_dict.items():
            for ptcl in protocols:
                if (ptcl in s.protocol_name):
                    if key in protocols_with_mag_and_phase.keys():
                        if 'M' in s.image_type:
                            new_key = protocols_with_mag_and_phase[key][0] # first entry is mag
                        else:
                            new_key = protocols_with_mag_and_phase[key][1] # second entry is phase

                        info[new_key].append(s.series_id)

                    else:
                        info[key].append(s.series_id)

    return info
