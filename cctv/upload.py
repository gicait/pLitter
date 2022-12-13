import os
import json
#import base64
import requests
import time
import yaml
import sqlite3
import numpy as np
import cv2
import json

class_map = {'Debris': 'plastic', 'Bottle': 'Plastic bottle', 'Styrofoam': 'Styrofoam', 'Trash bag': 'Trash bag'}

# ------make sure below env vars are set before run----------
root_dir = os.getenv('root_dir', 'project_home')
url = os.getenv('url', None)
dataset_id = os.getenv('id', None)
key = os.getenv('key', '--secrte-key--')

print(root_dir, url, dataset_id)

if not (url and dataset_id):
    print("need api details to uplaod")
    exit()

image_url = url+'/api/image/'
prediction_url = url+'/api/annotator/predictions'

image_dir = root_dir+'/data'
headers = {"Content-Type": "application/json; charset=utf-8"}

detections_dbpath = root_dir+'/db/detections.db' # change this
images_dbpath = root_dir+'/db/images.db'

print(detections_dbpath, images_dbpath)

conn = sqlite3.connect(images_dbpath, isolation_level=None)
conn.execute("VACUUM")
cur = conn.cursor()

det_conn = sqlite3.connect(detections_dbpath, isolation_level=None)
det_conn.execute("VACUUM")
det_cur = det_conn.cursor()

#time.sleep(10) # wait 10 sec
# dos moething to check netwrok connection

while True:
    try:
        cur.execute("""SELECT file_name FROM images WHERE uploaded=?""", (False,))
    except:
        print("db error")
        time.sleep(60)
        continue
    for row in cur.fetchall():
        image = row[0]+'.jpg'
        print(image)
        if image.endswith(('.png', '.jpg')) and os.path.isfile(os.path.join(image_dir,image)):
            files = {'image': open(os.path.join(image_dir,image), 'rb')}
            data = {'dataset_id': dataset_id, 'key': key}
            try:
                r = requests.post(image_url, files=files, data=data, timeout=119)
                print(r.status_code)
                if r.status_code == 200:
                    print("image uploaded successfully")
                    cur.execute("""UPDATE images SET uploaded=? WHERE file_name=?""", (1, row[0]))
                    r_json = r.json()
                    print(r_json)
                    if True:
                        image_id = r_json['image_id']
                        # get detections from db and upload
                        print(image_id)
                        detections = []
                        det_cur.execute("""SELECT * from detections WHERE date_time=?""", (row[0],))
                        for det in det_cur.fetchall():
                            print(det)
                            detections.append({
                                'track_id': det[1],
                                'category': class_map[det[3]] if det[3] in class_map.keys() else 'plastic',
                                'isbbox': True,
                                'bbox': json.loads(det[4]),
                                'segmentation': json.loads(det[5]),
                                })
                            data = {'image_id': image_id, 'key': key, 'predictions': detections}
                        print(data)
                        rr = requests.post(prediction_url, json=data, timeout=119)
                        print(rr.status_code, rr.json())
                        if rr.status_code == 200:
                            print('detections uploaded successfully')
                            cur.execute("""DELETE FROM images WHERE file_name=?""", (row[0],))
                            det_cur.execute("""DELETE FROM detections WHERE date_time=?""", (row[0],))
                    else:
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
