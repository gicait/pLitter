import os
import sys
import time
from datetime import datetime
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import numpy as np
import cv2
import json
import torch
import torchvision

import sqlite3

root_dir = os.getenv('root_dir', '/home/cctv/plitter/') #set env var with desired path
weights = os.getenv('weights', root_dir+'/models/yolov5s.pt')
FRAME_WIDTH = os.getenv('frame_width', 1920)
FRAME_HEIGHT = os.getenv('frame_height', 1280)
interval = int(os.getenv('interval', 60))
work_in_night = os.getenv('work_in_night', True)

print(root_dir, weights, FRAME_WIDTH, FRAME_HEIGHT, interval, work_in_night)

db_dir = os.path.join(root_dir, 'db')
data_dir = os.path.join(root_dir, 'data')
os.makedirs(db_dir, exist_ok=True)
os.makedirs(data_dir, exist_ok=True)

#print(root_dir, db_dir, data_dir)

detections_dbpath = os.path.join(db_dir, 'detections.db') # change this
images_dbpath = os.path.join(db_dir, 'images.db')

print(detections_dbpath)
conn = sqlite3.connect(detections_dbpath, isolation_level=None)
cur = conn.cursor()
cur.execute("""CREATE TABLE IF NOT EXISTS detections(id INTEGER PRIMARY KEY, track_id INTEGER, date_time TEXT, cat_id INTEGER, bbox TEXT, segmentation TEXT)""")
conn.commit()

im_conn = sqlite3.connect(images_dbpath, isolation_level=None)
im_cur = im_conn.cursor()
im_cur.execute("""CREATE TABLE IF NOT EXISTS images(id INTEGER PRIMARY KEY, file_name TEXT UNIQUE, uploaded BOOLEAN)""")
im_conn.commit()

# torch.set_printoptions(precision=3)

slice_boxes = [[0, 0, 720, 840], [648, 0, 1368, 840], [1200, 0, 1920, 840], [0, 440, 720, 1280], [648, 440, 1368, 1280], [1200, 440, 1920, 1280]]

device = torch.device('cuda:0')
half = True

model = torch.hub.load('ultralytics/yolov5', 'custom', weights)
print(model.names)

t0 = time.time()

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, int(FRAME_WIDTH))
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, int(FRAME_HEIGHT))

cur = conn.cursor()
im_cur = im_conn.cursor()

with torch.no_grad():
    while True:
        current_time = datetime.now().strftime("%H:%M:%S")
        start = '06:00:00'
        end = '18:00:00'
        if current_time >= end or current_time < start:
            if work_in_night in (False, 'False'):
                print('night mode turning off')
                time.sleep(60)
                continue

        st = time.time()
        im_name = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        ret, img0 = cap.read()
        #img0 = cv2.imread(root_dir+'/cctv/test.jpg') #image for test
        
        if img0.all() is None:
            continue
        preds = torch.tensor([], dtype=torch.float16)
        for box in slice_boxes:
            img = img0[box[1]:box[3], box[0]:box[2], :]
            pred = model(img)
            proc_pred = pred.xyxy[0].cpu()
            for i, det in enumerate(proc_pred):
                proc_pred[i][0] += box[0]
                proc_pred[i][1] += box[1]
                proc_pred[i][2] += box[0]
                proc_pred[i][3] += box[1]
            preds = torch.cat((preds, proc_pred), 0)
        for pred in preds:
            pred = pred.tolist()
            bbox = [pred[0], pred[1], pred[2]-pred[0], pred[3]-pred[1]]
            segmentation = [[pred[0], pred[1], pred[2], pred[1], pred[2], pred[3], pred[0], pred[3]]]
            cur.execute("""INSERT INTO detections (track_id, date_time, cat_id, bbox, segmentation) values(?,?,?,?,?)""", ( 0, im_name, int(pred[4]), json.dumps(bbox), json.dumps(segmentation)))
        im_save = cv2.imwrite(data_dir+'/'+im_name+'.jpg', img0)
        if im_save:
            im_cur.execute("""INSERT INTO images (file_name, uploaded) values(?,?)""", (im_name, False))
        fn = time.time()
        print("time:", fn-st)
        time.sleep(interval)
