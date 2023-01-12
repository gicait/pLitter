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
from detector import detector
import sqlite3
import argparse
import torch

def gstreamer_pipeline(
    sensor_id=0,
    capture_width=1920,
    capture_height=1080,
    display_width=1920,
    display_height=1080,
    framerate=30,
    flip_method=0,
    ):
    return (
        f"nvarguscamerasrc sensor-id={sensor_id} ! "
        "video/x-raw(memory:NVMM), "
        f"width=(int){capture_width}, height=(int){capture_height}, "
        f"format=(string)NV12, framerate=(fraction){framerate}/1 ! "
        f"nvvidconv flip-method={flip_method} ! "
        f"video/x-raw, width=(int){display_width}, height=(int){display_height}, format=(string)BGRx ! "
        "videoconvert ! "
        "video/x-raw, format=(string)BGR ! appsink sync=0"
    )

def get_slice_bboxes(image_height,image_width,slice_height,slice_width,overlap_height_ratio,overlap_width_ratio):
    slice_bboxes = []
    y_max = y_min = 0
    y_overlap = int(overlap_height_ratio * slice_height)
    x_overlap = int(overlap_width_ratio * slice_width)
    while y_max < image_height:
        x_min = x_max = 0
        y_max = y_min + slice_height
        while x_max < image_width:
            x_max = x_min + slice_width
            if y_max > image_height or x_max > image_width:
                xmax = min(image_width, x_max)
                ymax = min(image_height, y_max)
                xmin = max(0, xmax - slice_width)
                ymin = max(0, ymax - slice_height)
                slice_bboxes.append([xmin, ymin, xmax, ymax])
            else:
                slice_bboxes.append([x_min, y_min, x_max, y_max])
            x_min = x_max - x_overlap
        y_min = y_max - y_overlap
    return slice_bboxes

# slice_boxes = get_slice_bboxes(FRAME_HEIGHT, FRAME_WIDTH, slice_height, silce_width, 0.04, 0.04) 
# slice_boxes = [[0, 0, 720, 840], [648, 0, 1368, 840], [1200, 0, 1920, 840], [0, 440, 720, 1280], [648, 440, 1368, 1280], [1200, 440, 1920, 1280]]

def cctv(csi_cam, sensor_id, model, dest, img_width, img_height, det_cur, im_cur, slice_width, slice_height, input_size, interval, work_in_night):
    t0 = time.time()

    if not csi_cam:
        cap = cv2.VideoCapture(sensor_id)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, int(img_width))
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, int(img_height))
    else:
        cap = cv2.VideoCapture(gstreamer_pipeline(sensor_id, img_width, img_height, img_width, img_height, 30, 0), cv2.CAP_GSTREAMER)
    
    slice_boxes = get_slice_bboxes(img_height, img_width, slice_height, slice_width, 0.04, 0.04) 

    # with torch.no_grad():
    st = time.time() - interval
    while True:
        current_time = datetime.now().strftime("%H:%M:%S")
        start = '06:00:00'
        end = '18:00:00'
        if current_time >= end or current_time < start:
            if work_in_night in (False, 'False'):
                print('night mode turning off')
                time.sleep(60)
                continue

        im_name = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        ret, img0 = cap.read()
        if not time.time()-st >= interval:
            print('skipping', img0.shape)
            continue
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
            det_cur.execute("""INSERT INTO detections (track_id, date_time, cat_id, bbox, segmentation) values(?,?,?,?,?)""", ( 0, im_name, int(pred[4]), json.dumps(bbox), json.dumps(segmentation)))
        im_save = cv2.imwrite(dest+'/'+im_name+'.jpg', img0)
        if im_save:
            im_cur.execute("""INSERT INTO images (file_name, uploaded) values(?,?)""", (im_name, False))
        print("time:", time.time()-st)
        st = time.time()

if __name__ == '__main__':

    parser = argparse.ArgumentParser()

    parser.add_argument('--csi-cam', action='store_true', help='CSI camera (True) or USB camera (False, default)')
    parser.add_argument('--sensor-id', type=int, default=0, help='camera number')
    parser.add_argument('--dest', type=str, default='./data', help='destination folder')
    parser.add_argument('--img-width', type=int, default=1920, help='image width')
    parser.add_argument('--img-height', type=int, default=1080, help='image height')
    parser.add_argument('--slice-width', type=int, default=840, help='slice width')
    parser.add_argument('--slice-height', type=int, default=720, help='slice height')
    parser.add_argument('--input-size', type=int, default=640, help='input size')
    parser.add_argument('--interval', type=int, default=60, help='interval in seconds')
    parser.add_argument('--work-in-night', type=bool, default=True, help='work in night')

    args = parser.parse_args()
    model = detector.load('cctv')

    detections_dbpath = os.path.join(args.dest, 'detections.db') # change this
    images_dbpath = os.path.join(args.dest, 'images.db')

    print(detections_dbpath, images_dbpath)

    det_conn = sqlite3.connect(detections_dbpath, isolation_level=None)
    det_cur = det_conn.cursor()
    det_cur.execute("""CREATE TABLE IF NOT EXISTS detections(id INTEGER PRIMARY KEY, track_id INTEGER, date_time TEXT, cat_id INTEGER, bbox TEXT, segmentation TEXT)""")
    det_conn.commit()

    im_conn = sqlite3.connect(images_dbpath, isolation_level=None)
    im_cur = im_conn.cursor()
    im_cur.execute("""CREATE TABLE IF NOT EXISTS images(id INTEGER PRIMARY KEY, file_name TEXT UNIQUE, uploaded BOOLEAN)""")
    im_conn.commit()

    cctv(csi_cam=args.csi_cam,
        sensor_id=args.sensor_id, 
        model=model, dest=args.dest, 
        img_width=args.img_width, 
        img_height=args.img_height,
        det_cur=det_cur,
        im_cur=im_cur,
        slice_width=args.slice_width, 
        slice_height=args.slice_height, 
        input_size=args.input_size, 
        interval=args.interval, 
        work_in_night=args.work_in_night
    )
