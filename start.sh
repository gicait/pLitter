#!/bin/bash
echo "Script executed from: ${PWD}"

BASEDIR=$(dirname $0)
echo "Script location: ${BASEDIR}"
cd ${BASEDIR}

git pull

/usr/bin/python3 cctv/cameraConf.py
/usr/bin/python3 cctv/getWeights.py
#/usr/bin/python3 cctv/testWeights.py
OPENBLAS_CORETYPE=ARMV8 MPLBACKEND=agg /usr/bin/python3 cctv/camera.py & /usr/bin/python3 serve/main.py
