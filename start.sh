#!/bin/bash
echo "Script executed from: ${PWD}"

BASEDIR=$(dirname $0)
echo "Script location: ${BASEDIR}"
cd ${BASEDIR}

set -o allexport
root_dir=${BASEDIR}
source cctv_secret.env
source camera_config.env
set +o allexport

mkdir -p data
mkdir -p db
mkdir -p logs

echo $root_dir

export OPENBLAS_CORETYPE=ARMV8
OPENBLAS_CORETYPE=ARMV8 MPLBACKEND=agg /usr/bin/python3 cctv/capture.py > logs/capture.log &
/usr/bin/python3 cctv/clean.py &
sleep 60
OPENBLAS_CORETYPE=ARMV8 /usr/bin/python3 cctv/upload.py > logs/upload.log &
