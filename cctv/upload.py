import os
import json
#import base64
import requests
import time
import yaml
import sqlite3
import numpy as np
import cv2

root_dir = os.getenv('root_dir', '/home/cctv/plitter') # chnage root path

url=None
dataset_id=None
home = os.path.expanduser("~") #somewhere outside project
# get api address
with open(os.path.join(home, '.cctv'), 'r') as stream:
    data = yaml.safe_load(stream)
    url = data['url']
    dataset_id = int(data['id'])
print(url, dataset_id)

if not (url and dataset_id):
    print("need api details to uplaod")
    exit()

image_url = url+'/api/image/'
prediction_url = url+'/api/annotator/predictions'

image_dir = root_dir+'/data'
headers = {"Content-Type": "application/json; charset=utf-8"}

debris_dbpath = root_dir+'/db/detections.db' # change this
images_dbpath = root_dir+'/db/images.db'

conn = sqlite3.connect(images_dbpath, isolation_level=None)
cur = conn.cursor()

#time.sleep(10) # wait 10 sec
# dos moething to check netwrok connection

while True:
    cur.execute("""SELECT file_name FROM images WHERE uploaded=?""", (False,))
    for row in cur.fetchall():
        image = row[0]+'.jpg'
        print(image)
        if image.endswith(('.png', '.jpg')) and os.path.isfile(os.path.join(image_dir,image)):
            files = {'image': open(os.path.join(image_dir,image), 'rb')}
            data = {'dataset_id': dataset_id}
            try:
                r = requests.post(image_url, files=files, data=data, timeout=119)
                print(r.status_code)
                if r.status_code in (200, 400):
                    print("image uploaded successfully")
                    cur.execute("""UPDATE images SET uploaded=? WHERE file_name=?""", (1, row[0]))
                    r_json = r.json()
                    try:
                        image_id = r_json['image_id']
                        # get detections from db and upload
                    except:
                        pass
                    #os.remove(image_dir+image) #delete image after uploading optioanlly
                else:
                    print("failed to uplaod the image")
            except requests.exceptions.ConnectionError as errc:
                print("Error connecting:", errc)
            except requests.exceptions.HTTPError as errh:
                print("Http error:", errh)
            except requests.exceptions.Timeout as errt:
                print("Timeout error:", errt)
            except requests.exceptions.RequestException as err:
                print("Uknown:", err)
    print("sleep for a minute") 
    time.sleep(60)
