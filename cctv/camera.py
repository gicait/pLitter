import os
import yaml

CAMERA_NAME="test"
WAIT_AT_START=25
CAMERA_SOURCE=0 #0 WEBCAM, 1 CSI-CAM, 2 IMAGES FROM DIR
INPUT_WIDTH=1920
INPUT_HEIGHT=1280
MODE=0 #0 TIMELAPSE IMAGES, 1 VIDEO
FRAME_INTERVAL=15 #SECONDS
VIDEO_LENGTH=300 #SECONDS
#TARGET_DIR="/home/cctv/plitter_cctv/images"
SAVE_EMPTY=True
NIGHT_MODE=False

import sys
sys.path.append('/home/cctv/')
sys.path.append('/home/cctv/plitter/yolov5/')
sys.path.append('/home/cctv/classy-sort-yolov5/sort')

import argparse
import platform
import shutil
import time
from datetime import datetime
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import cv2
import json
import torch
import torch.backends.cudnn as cudnn

from utils.general import check_img_size, non_max_suppression
try:
    from utils.general import scale_coords
except:
    from utils.general import scale_boxes

from utils.torch_utils import select_device

from sort import *

import sqlite3

root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
db_dir = os.path.join(root_path, 'db')
data_dir = os.path.join(root_path, 'data')
os.makedirs(db_dir, exist_ok=True)
os.makedirs(data_dir, exist_ok=True)

print(root_path, db_dir, data_dir)

debris_dbpath = os.path.join(db_dir, 'debris.db') # change this
images_dbpath = os.path.join(db_dir, 'images.db')

conn = sqlite3.connect(debris_dbpath, isolation_level=None)
cur = conn.cursor()
cur.execute("""CREATE TABLE IF NOT EXISTS debris(id INTEGER PRIMARY KEY, track_id INTEGER, im_name TEXT, cat_id INTEGER, bbox TEXT, segmentation TEXT)""")
conn.commit()

im_conn = sqlite3.connect(images_dbpath, isolation_level=None)
im_cur = im_conn.cursor()
im_cur.execute("""CREATE TABLE IF NOT EXISTS images(id INTEGER PRIMARY KEY, im_name TEXT UNIQUE, uploaded BOOLEAN)""")
im_conn.commit()

torch.set_printoptions(precision=3)

palette = (2 ** 11 - 1, 2 ** 15 - 1, 2 ** 20 - 1)

if INPUT_WIDTH == 3840:
    slice_boxes = [[0, 0, 960, 840], [864, 0, 1824, 840], [1728, 0, 2688, 840], [2592, 0, 3552, 840], [2880, 0, 3840, 840], [0, 756, 960, 1596], [864, 756, 1824, 1596], [1728, 756, 2688, 1596], [2592, 756, 3552, 1596], [2880, 756, 3840, 1596], [0, 1320, 960, 2160], [864, 1320, 1824, 2160], [1728, 1320, 2688, 2160], [2592, 1320, 3552, 2160], [2880, 1320, 3840, 2160]]
else:
    slice_boxes = [[0, 0, 720, 840], [648, 0, 1368, 840], [1200, 0, 1920, 840], [0, 440, 720, 1280], [648, 440, 1368, 1280], [1200, 440, 1920, 1280]]

def bbox_rel(*xyxy):
    """" Calculates the relative bounding box from absolute pixel values. """
    bbox_left = min([xyxy[0].item(), xyxy[2].item()])
    bbox_top = min([xyxy[1].item(), xyxy[3].item()])
    bbox_w = abs(xyxy[0].item() - xyxy[2].item())
    bbox_h = abs(xyxy[1].item() - xyxy[3].item())
    x_c = (bbox_left + bbox_w / 2)
    y_c = (bbox_top + bbox_h / 2)
    w = bbox_w
    h = bbox_h
    return x_c, y_c, w, h

def xyxy2xywh(xyxy):
    x1, y1, x2, y2 = [int(i) for i in xyxy]
    x_min = min(x1,x2)
    y_min = min(y1,y2)
    w = abs(x1-x2)
    h = abs(y1-y2)
    return [int(x_min), int(y_min), int(w), int(h)]

def compute_color_for_labels(label):
    """
    Simple function that adds fixed color depending on the class
    """
    color = [int((p * (label ** 2 - label + 1)) % 255) for p in palette]
    return tuple(color)


def draw_boxes(img, bbox, identities=None, categories=None, names=None, offset=(0, 0)):
    for i, box in enumerate(bbox):
        x1, y1, x2, y2 = [int(i) for i in box]
        x1 += offset[0]
        x2 += offset[0]
        y1 += offset[1]
        y2 += offset[1]
        # box text and bar
        cat = int(categories[i]) if categories is not None else 0
        
        id = int(identities[i]) if identities is not None else 0
        
        color = compute_color_for_labels(id)
        
        label = f'{names[cat]} | {id}'
        t_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_PLAIN, 1, 1)[0]
        cv2.rectangle(img, (x1, y1), (x2, y2), color, 1)
        #cv2.rectangle(img, (x1, y1), (x1 + t_size[0] + 3, y1 + t_size[1] + 4), color, -1)
        cv2.putText(img, label, (x1, y1 + t_size[1] + 6), cv2.FONT_HERSHEY_PLAIN, 1, [255, 255, 255], 1)
    return img

def detect(opt, *args):
    out, source, weights, view_img, save_txt, imgsz, save_img, sort_max_age, sort_min_hits, sort_iou_thresh= \
        opt.output, opt.source, opt.weights, opt.view_img, opt.save_txt, opt.img_size, opt.save_img, opt.sort_max_age, opt.sort_min_hits, opt.sort_iou_thresh
    
    # Initialize SORT
    sort_tracker = Sort(max_age=sort_max_age,
                       min_hits=sort_min_hits,
                       iou_threshold=sort_iou_thresh) # {plug into parser}
    
    
    # Directory and CUDA settings for yolov5
    device = select_device(opt.device)
    #if os.path.exists(out):
    #    shutil.rmtree(out)  # delete output folder
    #os.makedirs(out)  # make new output folder
    half = device.type != 'cpu'  # half precision only supported on CUDA

    # Load yolov5 model
    if os.path.isdir(weights):
        weights = sorted(os.listdir(weights))[-1]
    print(weights)
    model = torch.load(weights, map_location=device)['model'].float() #load to FP32. yolov5s.pt file is a dictionary, so we retrieve the model by indexing its key
    model.to(device).eval()
    if half:
        model.half() #to FP16

    # Set DataLoader
    vid_path, vid_writer = None, None
    
    #if webcam:
    #    view_img = True
    #    cudnn.benchmark = True  # set True to speed up constant image size inference
    #    dataset = LoadStreams(source, img_size=imgsz)
    #else:
    #    dataset = LoadImages(source, img_size=imgsz)
    
    # get names of object categories from yolov5.pt model
    names = model.module.names if hasattr(model, 'module') else model.names
    print(names)
    
    # Run inference
    t0 = time.time()
    img = torch.zeros((1,3,imgsz,imgsz), device=device) #init img
    
    # Run once (throwaway)
    _ = model(img.half() if half else img) if device.type != 'cpu' else None
    
    save_path = str(Path(out))
    txt_path = str(Path(out))+'/results.txt'
        
    #for frame_idx, (path, img, im0s, vid_cap) in enumerate(dataset): #for every frame
    dataset = []
    #for img in sorted(os.listdir(source)):
    #    if img.endswith(('.jpg', '.png')):
    #        dataset.append(img)

    old_ids = []

    if CAMERA_SOURCE == 0:
        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
    
    if not cap.isOpened():
        raise Exception("could not open video device")
    
    #for im_name in sorted(dataset):
    cur = conn.cursor()
    last_image_time = 0.0
    while True:
        current_time = datetime.now().strftime("%H:%M:%S")
        start = '06:00:00'
        end = '18:00:00'
        if current_time >= end and current_time < start:
            if NIGHT_MODE == False:
                print('night mode turning off')
                break
        st = time.time()
        im_name = datetime.now().strftime("%Y%m%d_%H%M%S")+'.jpg'
        #print(im_name)
        #img0 = cv2.imread(os.path.join(source, im_name))
        try:
            ret, img0 = cap.read()
            if img0.all() is None:
                continue
            preds = np.empty((0,6))

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
            
                # Inference
                #t1 = time_synchronized()
                pred = model(img, augment=opt.augment)[0]

                # Apply NMS
                pred = non_max_suppression(pred, opt.conf_thres, opt.iou_thres, classes=opt.classes, agnostic=opt.agnostic_nms)

                for i, det in enumerate(pred):
                    #det[:, :4] = scale_coords(img.shape[2:], det[:, :4], shp).round()
                    for x1,y1,x2,y2,conf,detclass in det.cpu().detach().numpy():
                        print(x1,y1,x2,y2,conf,detclass)
                        preds = np.vstack((preds, np.array([box[0]+(x1*w_r), box[1]+(y1*h_r), box[0]+(x2*w_r), box[1]+(y2*h_r), conf, detclass])))
        
            print('preds:\n',preds,'\n')
            tracked_dets = sort_tracker.update(preds)
            print('Output from SORT:\n',tracked_dets,'\n')
            filtered_dets = np.empty((0,9))
            old_ids = []
            for det in tracked_dets:
                if det[-1] not in old_ids and not np.isnan(det).any():
                    old_ids.append(det[-1])
                    print(det)
                    filtered_dets = np.append(filtered_dets, [det], axis=0)

            print('new dets:\n',filtered_dets,'\n')
                
            # draw boxes for visualization
            if len(filtered_dets)>0:
                bbox_xyxy = filtered_dets[:,:4]
                identities = filtered_dets[:, 8]
                categories = filtered_dets[:, 4]
                track_ids = filtered_dets[:, -1]
                coco_json = {im_name: []}
                for pred in filtered_dets:
                    coco_format = {}
                    bbox = xyxy2xywh(pred[:4])
                    coco_format['category_id'] = int(pred[4])
                    coco_format['isbbox'] = True
                    coco_format['segmentation'] = [[bbox[0], bbox[1], bbox[0]+bbox[2], bbox[1], bbox[0]+bbox[2], bbox[1]+bbox[3], bbox[0], bbox[1]+bbox[3]]]
                    coco_format['bbox'] = [bbox[0], bbox[1], bbox[2], bbox[3]]
                    coco_json[im_name].append(coco_format)
                    cur.execute("""INSERT INTO debris (track_id, im_name, cat_id, bbox, segmentation) values(?,?,?,?,?)""", ( int(pred[8]), im_name, int(pred[4]), json.dumps(coco_format['bbox']), json.dumps(coco_format['segmentation'])) )
                    print(( int(pred[8]), int(pred[4]), im_name, json.dumps(coco_format['bbox']), json.dumps(coco_format['segmentation'])))
                    #conn.cmmit()
                print(coco_json)
                #json.dump(coco_json, open(os.path.join(save_path, im_name.replace('.jpg', '.json')), 'w'))
                #img0 = draw_boxes(img0, bbox_xyxy, identities, categories, names)
                #last_image_time = time.time()
            if time.time()-last_image_time > FRAME_INTERVAL:
                ch = cv2.imwrite(os.path.join(save_path, im_name), img0)
                if ch:
                    im_cur.execute("""INSERT INTO images (im_name, uploaded) values(?,?)""", (im_name, False))
                    last_image_time = time.time()
        except:
            try:
                if time.time()-last_image_time > FRAME_INTERVAL:
                    ch = cv2.imwrite(os.path.join(save_path, im_name), img0)
                    if ch:
                        im_cur.execute("""INSERT INTO images (im_name, uploaded) values(?,?)""", (im_name, False))
                        last_image_time = time.time()
            except:
                print('im_name time error may be')
        ch = False
        print('time:', time.time()-st)
        print('--------------------------------------------------', '\n')

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--weights', type=str,
                        default='/home/cctv/plitter/models/best.pt', help='model.pt path')
    # file/folder, 0 for webcam
    parser.add_argument('--source', type=str,
                        default='/home/cctv/plitter/data', help='source')
    parser.add_argument('--output', type=str, default='/home/cctv/plitter/data',
                        help='output folder')  # output folder
    parser.add_argument('--img-size', type=int, default=640,
                        help='inference size (pixels)')
    parser.add_argument('--conf-thres', type=float,
                        default=0.1, help='object confidence threshold')
    parser.add_argument('--iou-thres', type=float,
                        default=0.2, help='IOU threshold for NMS')
    parser.add_argument('--fourcc', type=str, default='mp4v',
                        help='output video codec (verify ffmpeg support)')
    parser.add_argument('--device', default='',
                        help='cuda device, i.e. 0 or 0,1,2,3 or cpu')
    parser.add_argument('--view-img', action='store_true',
                        help='display results')
    parser.add_argument('--save-img', action='store_true',
                        help='save video file to output folder (disable for speed)')
    parser.add_argument('--save-txt', action='store_true',
                        help='save results to *.txt')
    parser.add_argument('--classes', nargs='+', type=int,
                        default=[i for i in range(80)], help='filter by class') #80 classes in COCO dataset
    parser.add_argument('--agnostic-nms', action='store_true',
                        help='class-agnostic NMS')
    parser.add_argument('--augment', action='store_true',
                        help='augmented inference')
    
    #SORT params
    parser.add_argument('--sort-max-age', type=int, default=5,
                        help='keep track of object even if object is occluded or not detected in n frames')
    parser.add_argument('--sort-min-hits', type=int, default=0,
                        help='start tracking only after n number of objects detected')
    parser.add_argument('--sort-iou-thresh', type=float, default=0.0	,
                        help='intersection-over-union threshold between two frames for association')
    
    args = parser.parse_args()
    args.img_size = check_img_size(args.img_size)
    print(args)

    source_path = Path(__file__).resolve()
    source_dir = source_path.parent

    with open(os.path.join(source_dir, 'conf.yaml'), 'r') as stream:
        data = yaml.safe_load(stream)
        print(data)
        if 'frame_width' in data.keys():
            FRAME_WIDTH = data['frame_width']
        if 'frame_height' in data.keys():
            FRAME_HEIGHT = data['frame_height']


    WAIT_AT_START=3
    CAMERA_SOURCE=0 #0 WEBCAM, 1 CSI-CAM, 2 IMAGES FROM DIR
    INPUT_WIDTH=1920
    INPUT_HEIGHT=1280
    MODE=0 #0 TIMELAPSE IMAGES, 1 VIDEO
    FRAME_INTERVAL=15 #SECONDS
    VIDEO_LENGTH=300 #SECONDS
    #TARGET_DIR="/home/cctv/plitter_cctv/images"
    SAVE_EMPTY=True
    NIGHT_MODE=False

    with torch.no_grad():
        detect(args)