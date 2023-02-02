#!/bin/bash

if [ "$#" -ne 3 ]; then
   echo "Please specify current separate SES_A_DIR,SES_B_DIR, and relative path to subject dir  "
   exit 1
fi

SES_A_DIR=$1
SES_B_DIR=$2
SUB_DIR=$3

echo "This will copy (not mv) separately processed session (SES-B) next to (SES-A) in subject dir within $SES_A_DIR"

if [ ! -d "${SES_A_DIR}/${SUB_DIR}" ]; then
   echo "ses-B does not exist for ${SUB_DIR}"
   mkdir ${SES_A_DIR}/${SUB_DIR}
fi

rsync -a ${SES_B_DIR}/${SUB_DIR}/ses-* ${SES_A_DIR}/${SUB_DIR}/
rsync -a ${SES_B_DIR}/${SUB_DIR}/figures/* ${SES_A_DIR}/${SUB_DIR}/figures/
