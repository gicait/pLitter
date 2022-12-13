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
def draw_boxes_on_image(image, boxes, classes, class_ids, scores, use_normalized_coordinates=False, min_score_thresh=.3):
    assert len(boxes) == len(scores)
    for i in range(len(boxes)):
        box = boxes[i]
        category = str(classes[i])
        class_id = int(class_ids[i])
        score = scores[i]
        if score >= min_score_thresh:
          if use_normalized_coordinates:
            h,w,_ = image.shape
            y1 = int(box[0]*h)
            x1 = int(box[1]*w)
            y2 = int(box[2]*h)
            x2 = int(box[3]*w)
          else:
            x1,y1,x2,y2 = int(box[0]), int(box[1]), int(box[2]), int(box[3])
          image = cv2.rectangle(image, (x1, y1), (x2, y2), colors[class_id], 2)
          cv2.putText(image, category+':'+str(round(score,2)), (x1, y1-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, colors[class_id], 1)
    return image

#set env var with desired path

root_dir = os.getenv('root_dir', '/'.join(os.path.abspath(__file__).split('/')[0:-2]))

yolo_weights = Path(root_dir) / 'models' / os.getenv('weights', 'pLitterFloat_800x752_to_640x640.pt')
reid_weights = Path(root_dir) / 'models' / os.getenv('reid_weights', 'osnet_x0_25_msmt17.pt')

FRAME_WIDTH = int(os.getenv('frame_width', 1920))
FRAME_HEIGHT = int(os.getenv('frame_height', 1280))
interval = int(os.getenv('interval', 10))
work_in_night = os.getenv('work_in_night', True)
weights_url = os.getenv('weights_url', None)

print(root_dir, yolo_weights, reid_weights, FRAME_WIDTH, FRAME_HEIGHT, interval, work_in_night)

if os.path.join(root_dir, 'Yolov5_StrongSORT_OSNet') not in sys.path:
    print(os.path.join(root_dir, 'Yolov5_StrongSORT_OSNet'))
    sys.path.append(os.path.join(root_dir, 'Yolov5_StrongSORT_OSNet'))
if os.path.join(root_dir, 'Yolov5_StrongSORT_OSNet/yolov5') not in sys.path:
    print(os.path.join(root_dir, 'Yolov5_StrongSORT_OSNet/yolov5'))
    sys.path.append(os.path.join(root_dir, 'Yolov5_StrongSORT_OSNet/yolov5'))
if os.path.join(root_dir, 'Yolov5_StrongSORT_OSNet/trackers/strong_sort') not in sys.path:
    print(os.path.join(root_dir, 'Yolov5_StrongSORT_OSNet/trackers/strong_sort'))
    sys.path.append(os.path.join(root_dir, 'Yolov5_StrongSORT_OSNet/trackers/strong_sort'))

from yolov5.models.common import DetectMultiBackend
from yolov5.utils.general import (LOGGER, check_img_size, non_max_suppression, scale_boxes, check_requirements, cv2,
                                  check_imshow, xyxy2xywh, increment_path, strip_optimizer, colorstr, print_args, check_file)

from trackers.strong_sort.utils.parser import get_config
from trackers.strong_sort.strong_sort import StrongSORT

db_dir = os.path.join(root_dir, 'db')
data_dir = os.path.join(root_dir, 'data')
os.makedirs(db_dir, exist_ok=True)
os.makedirs(data_dir, exist_ok=True)

#print(root_dir, db_dir, data_dir)
#generate a unique string fro saving tracking ids (tracker starts from zero, every time it restarts, so it requires a unique id to distinguish)

uid = str(uuid.uuid4())

#db_path = os.path.join(db_dir, 'plitter.db')

detections_dbpath = os.path.join(db_dir, 'detections.db') # change this
images_dbpath = os.path.join(db_dir, 'images.db')

conn = sqlite3.connect(detections_dbpath, isolation_level=None)
cur = conn.cursor()
cur.execute("""CREATE TABLE IF NOT EXISTS detections(id INTEGER PRIMARY KEY, track_id TEXT, date_time TEXT, category TEXT, bbox TEXT, segmentation TEXT)""")
conn.commit()

im_conn = sqlite3.connect(images_dbpath, isolation_level=None)
im_cur = im_conn.cursor()
im_cur.execute("""CREATE TABLE IF NOT EXISTS images(id INTEGER PRIMARY KEY, file_name TEXT UNIQUE, uploaded BOOLEAN)""")
im_conn.commit()

# torch.set_printoptions(precision=3)

silce_width = int(os.getenv("silce_width", 800))
slice_height = int(os.getenv("slice_height", 752))

# slice_boxes = [[0, 0, 720, 840], [648, 0, 1368, 840], [1200, 0, 1920, 840], [0, 440, 720, 1280], [648, 440, 1368, 1280], [1200, 440, 1920, 1280]]
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


cfg = get_config()
cfg.merge_from_file(os.path.join(root_dir, 'Yolov5_StrongSORT_OSNet/trackers/strong_sort/configs/strong_sort.yaml'))

tracker = StrongSORT(
    reid_weights,
    device,
    half,
    max_dist=cfg.STRONGSORT.MAX_DIST,
    max_iou_distance=cfg.STRONGSORT.MAX_IOU_DISTANCE,
    max_age=cfg.STRONGSORT.MAX_AGE,
    max_unmatched_preds=cfg.STRONGSORT.MAX_UNMATCHED_PREDS,
    n_init=cfg.STRONGSORT.N_INIT,
    nn_budget=cfg.STRONGSORT.NN_BUDGET,
    mc_lambda=cfg.STRONGSORT.MC_LAMBDA,
    ema_alpha=cfg.STRONGSORT.EMA_ALPHA,
)

tracker.model.warmup()

t0 = time.time()

#cap = cv2.VideoCapture('/home/cctv/Bangbua_20221025_134829.mp4')
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, int(FRAME_WIDTH))
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, int(FRAME_HEIGHT))

imgsz = 640

cur = conn.cursor()
im_cur = im_conn.cursor()

prev_frame, curr_frame = None, None

start = '06:00:00'
end = '18:00:00'

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
        
        ret, img0 = cap.read()
        #img0 = cv2.imread(root_dir+'/cctv/test.jpg') #image for test
        curr_frame = img0

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

        if prev_frame is not None and curr_frame is not None:
            tracker.tracker.camera_update(prev_frame, curr_frame)
        
        preds = tracker.update(preds, img0)
        #print(preds)

        if len(preds) == 0:
            continue

        #print(preds[:, :4], model.names, preds[:, 5], preds[:, 6]) 
        print(preds)
        #imgr = draw_boxes_on_image(img0, preds[:, :4].tolist(), [model.names[int(i)] for i in preds[:, 5].tolist()], preds[:, 5].tolist(), preds[:, 4].tolist())

        for j, (pred) in enumerate(preds):
            #print(pred)
            #pred = list(map(int, pred.tolist()))
            bbox = [pred[0], pred[1], pred[2]-pred[0], pred[3]-pred[1]]
            segmentation = [[pred[0], pred[1], pred[2], pred[1], pred[2], pred[3], pred[0], pred[3]]]
            cur.execute("""INSERT INTO detections (track_id, date_time, category, bbox, segmentation) values(?,?,?,?,?)""", ( uid+'_'+str(pred[4]), im_name, model.names[int(pred[5])], json.dumps(bbox), json.dumps(segmentation)))
        im_save = cv2.imwrite(data_dir+'/'+im_name+'.jpg', img0)
        print(data_dir+'/'+im_name+'.jpg')
        if im_save:
            im_cur.execute("""INSERT INTO images (file_name, uploaded) values(?,?)""", (im_name, False))
        fn = time.time()
        print("time:", fn-st)
        prev_frame = curr_frame
        time.sleep(interval)
