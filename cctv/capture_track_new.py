import os
import sys
import time
from datetime import datetime
from pathlib import Path
import numpy as np
import cv2
import json
import torch
import uuid
from dotenv import load_dotenv
import sqlite3
import pickle

# LOAD ENVIRONMENT VARIABLES
load_dotenv("/home/cctv/plitter/camera_config.env")

# --- Images and data processing function ---
# CHECK IF THE BOUNDING BOX OVERLAPS WITH THE DEFINED ROI
def is_within_roi(box, roi):
    x_min, y_min, x_max, y_max = box
    roi_x_min, roi_y_min, roi_x_max, roi_y_max = roi
    return not (x_max < roi_x_min or x_min > roi_x_max or y_max < roi_y_min or y_min > roi_y_max)

def calculate_iou(box1, box2):
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])
    inter_area = max(0, x2 - x1) * max(0, y2 - y1)
    box1_area = (box1[2] - box1[0]) * (box1[3] - box1[1])
    box2_area = (box2[2] - box2[0]) * (box2[3] - box2[1])
    union_area = box1_area + box2_area - inter_area
    return inter_area / union_area if union_area > 0 else 0

def match_tracking_to_detection(track, detections, iou_thresh=0.5):
    best_iou = 0
    best_idx = None
    for i, det in enumerate(detections):
        iou = calculate_iou(track[:4], det['bbox_xyxy'])
        if iou > best_iou and iou >= iou_thresh:
            best_iou = iou
            best_idx = i
    return best_idx


def filter_duplicate_boxes(boxes, scores, class_ids, iou_threshold=0.5):
    filtered_boxes = []
    filtered_scores = []
    filtered_class_ids = []
    for i, box in enumerate(boxes):
        duplicate = False
        for j, selected_box in enumerate(filtered_boxes):
            iou = calculate_iou(box, selected_box)
            if iou > iou_threshold:
                duplicate = True
                break
        if not duplicate:
            filtered_boxes.append(box)
            filtered_scores.append(scores[i])
            filtered_class_ids.append(class_ids[i])
    return filtered_boxes, filtered_scores, filtered_class_ids

def get_slice_bboxes(image_height, image_width, slice_height, slice_width, overlap_height_ratio, overlap_width_ratio):
    slice_bboxes = []
    y_overlap = int(overlap_height_ratio * slice_height)
    x_overlap = int(overlap_width_ratio * slice_width)
    y_min = 0
    while y_min < image_height:
        x_min = 0
        y_max = y_min + slice_height
        while x_min < image_width:
            x_max = x_min + slice_width
            slice_bboxes.append([x_min, y_min, x_max, y_max])
            x_min = x_max - x_overlap
        y_min = y_max - y_overlap
    return slice_bboxes

def draw_boxes_on_image(image, boxes, classes, class_ids, scores, min_score_thresh=.3):
    colors = [(0, 255, 255), (0, 0, 255), (255, 0, 0), (0, 255, 0)] * 20
    for i, box in enumerate(boxes):
        if scores[i] >= min_score_thresh:
            x1, y1, x2, y2 = map(int, box)
            label = f"{classes[i]}: {scores[i]:.2f}"
            color = colors[class_ids[i] % len(colors)]
            image = cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)
            image = cv2.putText(image, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
    return image

# INTEGRATE SQL TO SAVE AND LOAD
def bbox_to_xyxy(bbox):
    x,y,w,h = bbox
    return [x,y,x+w,y+h]
def get_db_connection():
    conn = sqlite3.connect('tracker_db.sqlite')
    return conn

def setup_database(conn):
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tracked_objects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            track_id INTEGER NOT NULL,
            uuid TEXT UNIQUE NOT NULL,
            bbox TEXT,
            class_id INTEGER,
            reid_feature BLOB,
            last_seen TEXT,
            frame_id INTEGER NOT NULL
        )
    ''')
    conn.commit()

# COUNT DETECTION FRAME
frame_counter = 0

def save_tracker_state_to_db(trackings, conn, max_frames=20):
    global frame_counter
    frame_counter += 1
    cursor = conn.cursor()
    now = datetime.now().isoformat()

    uuid_map = {}  # track_id (StrongSORT) -> uuid

    for det in trackings:
        track_id = int(det[4])
        bbox = det[:4].tolist()
        class_id = int(det[5])

        reid_feature = det[6]
        if isinstance(reid_feature, torch.Tensor):
            reid_feature = reid_feature.cpu().numpy()

        bbox_str = json.dumps(bbox)
        reid_blob = pickle.dumps(reid_feature)

        # FIND OLD OBJECTS BY IOU+CLASS
        cursor.execute("""
            SELECT uuid, bbox FROM tracked_objects
            WHERE class_id = ?
            ORDER BY last_seen DESC
            LIMIT 30
        """, (class_id,))

        matched_uuid = None
        for uuid_db, bbox_db in cursor.fetchall():
            bbox_db = json.loads(bbox_db)
            if calculate_iou(bbox, bbox_db) > 0.5:
                matched_uuid = uuid_db
                break

        if matched_uuid:
            cursor.execute("""
                UPDATE tracked_objects
                SET bbox=?, reid_feature=?, last_seen=?, frame_id=?
                WHERE uuid=?
            """, (bbox_str, reid_blob, now, frame_counter, matched_uuid))
        else:
            matched_uuid = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO tracked_objects
                (track_id, uuid, bbox, class_id, reid_feature, last_seen, frame_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (track_id, matched_uuid, bbox_str, class_id,
                  reid_blob, now, frame_counter))

        uuid_map[track_id] = matched_uuid

    conn.commit()
    return uuid_map
def update_env():
    load_dotenv("/home/cctv/plitter/camera_config.env", override=True)

    global interval, work_in_night
    global slice_width, slice_height
    global xmin, ymin, xmax, ymax, roi
    global FRAME_WIDTH, FRAME_HEIGHT, slice_boxes,conf_thres, iou_thres

    interval = int(os.getenv('interval', 10))
    work_in_night = os.getenv('work_in_night', 'True')

    slice_width = int(os.getenv("slice_width", 1024))
    slice_height = int(os.getenv("slice_height", 1024))

    xmin = int(os.getenv('xmin'))
    ymin = int(os.getenv('ymin'))
    xmax = int(os.getenv('xmax'))
    ymax = int(os.getenv('ymax'))

    roi = [xmin, ymin, xmax, ymax]

    FRAME_WIDTH = int(os.getenv('frame_width', 1920))
    FRAME_HEIGHT = int(os.getenv('frame_height', 1080))
    conf_thres = float(os.getenv('conf_thres', 0.55))
    iou_thres = float(os.getenv('iou_thres', 0.5))
    slice_boxes = get_slice_bboxes(
        FRAME_HEIGHT, FRAME_WIDTH,
        slice_height, slice_width,
        0.04, 0.04
    )

    print("ENV RELOADED | ROI =", roi)
def load_reid_features_from_db(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT track_id, reid_feature FROM tracked_objects")

    reid_map = {}
    for track_id, reid_blob in cursor.fetchall():
        reid_feature = pickle.loads(reid_blob)
        reid_map[track_id] = reid_feature
    return reid_map

# LOAD CONFIGURATIONS
root_dir = os.getenv('root_dir', '/'.join(os.path.abspath(__file__).split('/')[:-2]))
yolo_weights = Path(root_dir) / 'models' / os.getenv('weights', 'best.pt')
reid_weights = Path(root_dir) / 'models' / os.getenv('reid_weights', 'osnet_x0_25_msmt17.pt')
FRAME_WIDTH, FRAME_HEIGHT = int(os.getenv('frame_width', 1920)), int(os.getenv('frame_height', 1280))

device = torch.device('cuda:0')
half = True
tracker_state_file = 'tracker_state.json'

# CONNECT AND SETUP DB
conn = get_db_connection()
setup_database(conn)

# LOAD MODEL
if os.path.join(root_dir, 'Yolov5_StrongSORT_OSNet') not in sys.path:
    sys.path.append(os.path.join(root_dir, 'Yolov5_StrongSORT_OSNet'))
if os.path.join(root_dir, 'Yolov5_StrongSORT_OSNet/yolov5') not in sys.path:
    sys.path.append(os.path.join(root_dir, 'Yolov5_StrongSORT_OSNet/yolov5'))
if os.path.join(root_dir, 'Yolov5_StrongSORT_OSNet/trackers/strong_sort') not in sys.path:
    sys.path.append(os.path.join(root_dir, 'Yolov5_StrongSORT_OSNet/trackers/strong_sort'))

from yolov5.models.common import DetectMultiBackend
from yolov5.utils.general import non_max_suppression
from trackers.strong_sort.utils.parser import get_config
from trackers.strong_sort.strong_sort import StrongSORT

model = DetectMultiBackend(yolo_weights, device=device, fp16=half)
stride, names, pt = model.stride, model.names, model.pt
cfg = get_config()
cfg.merge_from_file(os.path.join(root_dir, 'Yolov5_StrongSORT_OSNet/trackers/strong_sort/configs/strong_sort.yaml'))
tracker = StrongSORT(reid_weights, device, half, max_dist=cfg.STRONGSORT.MAX_DIST,
                     max_iou_distance=cfg.STRONGSORT.MAX_IOU_DISTANCE,
                     max_age=5, n_init=0,
                     nn_budget=cfg.STRONGSORT.NN_BUDGET)
tracker.model.warmup()

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)

imgsz = 640
data_dir = os.path.join(root_dir, 'data')
os.makedirs(data_dir, exist_ok=True)

timer = time.time()
start = '06:00:00'
end = '18:00:00'
def load_uuid_map_from_db(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT track_id, uuid FROM tracked_objects")
    return {row[0]: row[1] for row in cursor.fetchall()}
# ===============================
# MAIN LOOP
# ===============================
provisional_tracks = {}
PROVISIONAL_TTL = 150
with torch.no_grad():
    # Load previous state from database on startup
    reid_map = load_reid_features_from_db(conn)
    uuid_map = load_uuid_map_from_db(conn)

    while True:
        update_env()
        print('ROI :', roi)
        now_ts = time.time()
        current_time_str = datetime.now().strftime("%H:%M:%S")
        if current_time_str >= end or current_time_str < start:
            if work_in_night in (False, 'False'):
                print('Night mode is off, waiting...')
                time.sleep(60)
                continue

        im_name = datetime.now().strftime("%Y%m%d_%H%M%S")
        pred_json = {'image': im_name + '.jpg', 'preds': []}
        ret, img0 = cap.read()
        if not ret or img0 is None:
            print("No frame captured, check camera connection.")
            time.sleep(1)
            continue

        preds = torch.tensor([], dtype=torch.float16)

        for box in slice_boxes:
            img = img0[box[1]:box[3], box[0]:box[2], :]
            h, w, _ = img.shape
            h_r = h / imgsz
            w_r = w / imgsz
            img = cv2.resize(img, (imgsz, imgsz), interpolation=cv2.INTER_LINEAR)
            img = img.transpose((2, 0, 1))[::-1]
            img = np.ascontiguousarray(img)
            img = torch.from_numpy(img).to(device)
            img = img.half() if half else img.float()
            img /= 255.0
            if img.ndimension() == 3:
                img = img.unsqueeze(0)

            pred = model(img)
            pred = non_max_suppression(pred, conf_thres, iou_thres)

            proc_pred = pred[0].cpu()
            for i, det in enumerate(proc_pred):
                proc_pred[i][0] = proc_pred[i][0] * w_r + box[0]
                proc_pred[i][1] = proc_pred[i][1] * h_r + box[1]
                proc_pred[i][2] = proc_pred[i][2] * w_r + box[0]
                proc_pred[i][3] = proc_pred[i][3] * h_r + box[1]
            preds = torch.cat((preds, proc_pred), 0)

        boxes = preds[:, :4].numpy()
        scores = preds[:, 4].numpy()
        class_ids = preds[:, 5].numpy().astype(int)

        filtered_boxes, filtered_scores, filtered_class_ids = filter_duplicate_boxes(boxes, scores, class_ids, iou_threshold=0.5)
	
        dets = []
        for i in range(len(filtered_boxes)):
            det = list(filtered_boxes[i]) + [filtered_scores[i], filtered_class_ids[i]]
            dets.append(det)

        filtered_dets = [det for det in dets if is_within_roi(det[:4], roi)]
        # ===============================
        # SAVE ALL YOLO DETECTIONS
        # ===============================
        yolo_records = []
        for det in filtered_dets:
            x1, y1, x2, y2, score, cls = map(float, det)
            cls = int(cls)
            bbox_xyxy = [x1, y1, x2, y2]
        
            matched_uuid = None
            for uid, info in provisional_tracks.items():
                if info['class_id'] == cls:
                    if calculate_iou(bbox_xyxy, info['bbox']) > 0.5:
                        matched_uuid = uid
                        break
        
            if matched_uuid is None:
                matched_uuid = str(uuid.uuid4())
                provisional_tracks[matched_uuid] = {
                    'bbox': bbox_xyxy,
                    'class_id': cls,
                    'last_seen': time.time(),
                    'confirmed': False
                }
            else:
                provisional_tracks[matched_uuid]['bbox'] = bbox_xyxy
                provisional_tracks[matched_uuid]['last_seen'] = time.time()
        
            record = {
                'category': model.names[cls],
                'track_id': matched_uuid,
                'bbox': [x1, y1, x2 - x1, y2 - y1],
                'segmentation': [[x1, y1, x2, y1, x2, y2, x1, y2]],
                'matched':False
            }
            yolo_records.append(record)
            pred_json['preds'].append(record)
        # ===============================
        # STRONGSORT TRACKING
        # ===============================
        if len(filtered_dets)>0:
            dets_np = torch.tensor(filtered_dets, dtype=torch.float32)
        else:
            dets_np = torch.empty((0, 6), dtype=torch.float32)
        trackings = tracker.update(dets_np, img0)
        # ===============================
        # MATCH TRACK → YOLO
        # ===============================
        if trackings is not None and len(trackings) > 0:
            uuid_map = save_tracker_state_to_db(trackings, conn)

            for trk in trackings:
                trk = trk.tolist()
                strongsort_id = int(trk[4])
                uuid_id = uuid_map.get(strongsort_id)

                if uuid_id is None:
                    continue

                trk_box = trk[:4]

                for rec in yolo_records:
                    if rec['matched']:
                        continue
                    rec_bbox_xyxy = bbox_to_xyxy(rec['bbox'])
                    if calculate_iou(trk_box, rec_bbox_xyxy) > 0.5:
                        rec['track_id'] = uuid_id
                        rec['matched'] = True
                        break

        # ===============================
        # CLEAN PROVISIONAL (TIME-BASED)
        # ===============================
        provisional_tracks = {
            uid: info
            for uid, info in provisional_tracks.items()
            if now_ts - info['last_seen'] < PROVISIONAL_TTL
        }
        # ===============================
        # SAVE IMAGE + JSON
        # ===============================
        try:
            img_path = f"{data_dir}/{im_name}.jpg"
            json_path = f"{data_dir}/{im_name}.json"
            cv2.imwrite(img_path, img0)
            with open(json_path, 'w') as f:
                json.dump(pred_json, f)

        except Exception as e:
            print(f"Error saving files: {e}")

        time.sleep(interval)
