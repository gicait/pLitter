#!/bin/bash
echo "Script executed from: ${PWD}"

BASEDIR=$(dirname $0)
echo "Script location: ${BASEDIR}"
cd ${BASEDIR}

git submodule update --init --recursive
git submodule update --recursive --remote
#git pull
echo "pull done"

/usr/bin/python3 cctv/getConf.py & 
/usr/bin/python3 cctv/getWeights.py &
#/usr/bin/python3 cctv/testWeights.py
/usr/bin/python3 cctv/upload.py >> /home/cctv/ulog.txt 2>&1 &
sleep 60
OPENBLAS_CORETYPE=ARMV8 MPLBACKEND=agg /usr/bin/python3 cctv/camera.py >> /home/cctv/clog.txt 2>&1 & /usr/bin/python3 serve/main.py >> /home/cctv/slog.txt 2>&1 &
/usr/bin/python3 cctv/clean.py >> /home/cctv/cllog.txt 2>&1 &