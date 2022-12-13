import os, requests
import json
import time

url = os.getenv('url', None)
cctv_id = os.getenv('id', None)

print(url, cctv_id)

if not (url and cctv_id):
    print("set var")
    exit()


def check_connection(cctv_api):
    res = requests.get(cctv_api)
    if res.status_code == 200:
        return True
    return False

def getConfig(url):
    res = requests.get(url, timeout=120)
    if res.status_code == 200:
        return res.json()
    else:
        return {}

def readConfig(file_path):
    f = open(file_path, 'r')
    config = dict()
    for line in f:
        if "=" not in line:
            continue
        pair = line.split("=")
        config[pair[0]] = pair[1].strip()
    f.close()
    return config

def writeConfig(file_path, config):
    f = open('.'+file_path+'.swp', 'w')
    for k,v in config.items():
        f.write(str(k)+"="+str(v)+"\n")
    f.close()
    os.rename('.'+file_path+'.swp', file_path)

"""
                    frame_height=1080
                    frame_width=1920
                    images_prefix=''
                    interval=10
                    gitpull=False
                    send_empty=True
                    silce_width=800
                    slice_height=752
                    work_in_night=False
                    weights=pLitterFloat_800x752_to_640x640.pt
                    weights_url=https://github.com/gicait/pLitter/releases/download/v0.1/pLitterFloat_800x752_to_640x640.pt
"""

if os.path.isfile('camera_config.env'):
    config = readConfig('camera_config.env') #read filename from env var
else:
    config = {'frame_height': '1920', 'frame_width': '1080', 'images_prefix': "''", 'interval': '30', 'gitpull': 'False', 'send_empty': 'True', 'silce_width': '800', 'slice_height': '752', 'work_in_night': 'False', 'weights': 'pLitterFloat_800x752_to_640x640.pt', 'weights_url': 'https://github.com/gicait/pLitter/releases/download/v0.1/pLitterFloat_800x752_to_640x640.pt'}

time.sleep(180) # wait 3 min for start other programs
while True:
    #update config
    new_config = getConfig(url+'/api/dataset/'+str(cctv_id)+'/config')
    print(new_config)
    modify=False
    for k in config.keys():
        if k in new_config.keys():
            if config[k] != new_config[k]:
                config[k] = new_config[k]
                modify = True
    if modify:
        writeConfig('camera_config.env', config)
    time.sleep(300) #update for every 5 minutes
