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
# import torchvision
import sqlite3
import uuid

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

colors = [(0,255,255), (0,0,255), (255,0,0), (0,255,0)]*20

root_dir = os.getenv('root_dir', '/'.join(os.path.abspath(__file__).split('/')[0:-2]))

yolo_weights = Path(root_dir) / 'models' / os.getenv('weights', 'pLitterFloat_800x752_to_640x640.pt')

FRAME_WIDTH = int(os.getenv('frame_width', 1920))
FRAME_HEIGHT = int(os.getenv('frame_height', 1080))
interval = int(os.getenv('interval', 10))
work_in_night = os.getenv('work_in_night', True)
weights_url = os.getenv('weights_url', None)

print(root_dir, yolo_weights, FRAME_WIDTH, FRAME_HEIGHT, interval, work_in_night)

if os.path.join(root_dir, 'Yolov5_StrongSORT_OSNet') not in sys.path:
    print(os.path.join(root_dir, 'Yolov5_StrongSORT_OSNet'))
    sys.path.append(os.path.join(root_dir, 'Yolov5_StrongSORT_OSNet'))
if os.path.join(root_dir, 'Yolov5_StrongSORT_OSNet/yolov5') not in sys.path:
    print(os.path.join(root_dir, 'Yolov5_StrongSORT_OSNet/yolov5'))
    sys.path.append(os.path.join(root_dir, 'Yolov5_StrongSORT_OSNet/yolov5'))

from yolov5.models.common import DetectMultiBackend
from yolov5.utils.general import (LOGGER, check_img_size, non_max_suppression, scale_boxes, check_requirements, cv2,
                                  check_imshow, xyxy2xywh, increment_path, strip_optimizer, colorstr, print_args, check_file)

data_dir = os.path.join(root_dir, 'data')

# torch.set_printoptions(precision=3)

silce_width = int(os.getenv("silce_width", 800))
slice_height = int(os.getenv("slice_height", 752))

slice_boxes = get_slice_bboxes(FRAME_HEIGHT, FRAME_WIDTH, slice_height, silce_width, 0.04, 0.04)

device = torch.device('cuda:0')
half = True

#model = torch.hub.load('ultralytics/yolov5', 'custom', weights, skip_validation=True)
if not os.path.isfile(yolo_weights):
    #download weights here
    try:
        torch.hub.download_url_to_file(weights_url, yolo_weights)
    except:
        yolo_weights = Path(root_dir) / 'models/yolov5s.pt'
        pass

model = DetectMultiBackend(yolo_weights, device=device, fp16=half)
stride, names, pt = model.stride, model.names, model.pt
print(model.names)

t0 = time.time()

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, int(FRAME_WIDTH))
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, int(FRAME_HEIGHT))

imgsz = 640

prev_frame, curr_frame = None, None

start = '06:00:00'
end = '18:00:00'
timer = time.time()

with torch.no_grad():
    while True:
        current_time = datetime.now().strftime("%H:%M:%S")
        if current_time >= end or current_time < start:
            if work_in_night in (False, 'False'):
                print('night mode turning off')
                time.sleep(60)
                continue

        st = time.time()
        im_name = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        pred_json = {'image': im_name+'.jpg', 'preds': []}

        ret, img0 = cap.read()
        #imgr = img0
        #img0 = cv2.imread(root_dir+'/cctv/test.jpg') #image for test

        if img0 is None:
            print("check if camera is connected and run again \n")
            continue

        if img0.all() is None:
            continue
        
        preds = torch.tensor([], dtype=torch.float16)
        
        for box in slice_boxes:
            img = img0[box[1]:box[3], box[0]:box[2], :]
            h,w,_ = img.shape
            h_r = h/imgsz
            w_r = w/imgsz
            img = cv2.resize(img, (imgsz, imgsz), interpolation=cv2.INTER_LINEAR)
            img = img.transpose((2, 0, 1))[::-1]  # HWC to CHW, BGR to RGB
            img = np.ascontiguousarray(img)
            img = torch.from_numpy(img).to(device)
            img = img.half() if half else img.float() #unint8 to fp16 or fp32
            img /= 255.0 #normalize to between 0 and 1.
            if img.ndimension()==3:
                img = img.unsqueeze(0)
            
            pred = model(img)
            pred = non_max_suppression(pred, 0.4, 0.5)

            #print(pred)
            proc_pred = pred[0].cpu()
            
            for i, det in enumerate(proc_pred):
                proc_pred[i][0] = proc_pred[i][0]*w_r + box[0]
                proc_pred[i][1] = proc_pred[i][1]*h_r + box[1]
                proc_pred[i][2] = proc_pred[i][2]*w_r + box[0]
                proc_pred[i][3] = proc_pred[i][3]*h_r + box[1]
            preds = torch.cat((preds, proc_pred), 0)
        
        #print("preds:", preds)
        
        for pred in preds:
            pred = pred.tolist()
            bbox = [pred[0], pred[1], pred[2]-pred[0], pred[3]-pred[1]]
            seg = [[pred[0], pred[1], pred[2], pred[1], pred[2], pred[3], pred[0], pred[3]]]
            pred_json['preds'].append({'category': model.names[int(pred[5])], 'bbox': bbox, 'segmentation': seg})
        
        print(pred_json)
        im_save = cv2.imwrite(data_dir+'/'+im_name+'.jpg', img0)
        print(im_save)
        json.dump(pred_json, open(data_dir+'/'+im_name+'.json', 'w'))
        time.sleep(interval)
