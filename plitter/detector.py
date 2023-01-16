import os, sys
from pathlib import Path
import torch
import cv2

FILE = Path(__file__).resolve()
ROOT = FILE.parents[0]
WEIGHTS = ROOT.parents[0] / 'weights'

print('weights from', WEIGHTS)
WEIGHTS.mkdir(parents=True, exist_ok=True)

weights = {
    'street': {
        'weights': WEIGHTS / 'pLitterStreet_YOLOv5l.pt',
        'url': 'https://github.com/gicait/pLitter/releases/download/v0.0.0-street/pLitterStreet_YOLOv5l.pt'
    },
    'cctv': {
        'weights': WEIGHTS / 'pLitterFloat_800x752_to_640x640.pt',
        'url': 'https://github.com/gicait/pLitter/releases/download/v0.1/pLitterFloat_800x752_to_640x640.pt'
    }
}

colors = [(0,255,255), (0,0,255), (255,0,0), (0,255,0)]*20

@torch.no_grad()
def detector(type='street'):
    if type not in weights.keys():
        raise ValueError('Invalid type. Valid types are: ' + ', '.join(weights.keys()))
    if not os.path.isfile(weights[type]['weights']):
        weights_url = weights[type]['url']
        print('Downloading model from', weights_url)
        torch.hub.download_url_to_file(weights_url, str(weights[type]['weights']), hash_prefix=None, progress=True)

    # return torch.hub.load('ultralytics/yolov5', 'custom', str(weights[type]['weights']), force_reload=True)
    return torch.hub.load(str(ROOT / 'Yolov5_StrongSORT_OSNet/yolov5'), 'custom', str(weights[type]['weights']), source='local', force_reload=True)

trackers = ['strongsort']

def tracker(tracker_type='strongsort'):
    if tracker_type not in trackers:
        raise ValueError('Invalid type. Valid types are: ' + ', '.join(trackers))

    if str(ROOT / 'Yolov5_StrongSORT_OSNet') not in sys.path:
        sys.path.append(str(ROOT / 'Yolov5_StrongSORT_OSNet'))
    if str(ROOT / 'Yolov5_StrongSORT_OSNet/yolov5') not in sys.path:
        sys.path.append(str(ROOT / 'Yolov5_StrongSORT_OSNet/yolov5'))
    if str(ROOT / 'Yolov5_StrongSORT_OSNet/trackers/strongsort') not in sys.path:
        sys.path.append(str(ROOT / 'Yolov5_StrongSORT_OSNet/trackers/strongsort'))
    
    from trackers.multi_tracker_zoo import create_tracker

    tracker_config = ROOT / 'Yolov5_StrongSORT_OSNet/trackers/strongsort/configs/strongsort.yaml'
    reid_weights =  WEIGHTS / 'osnet_x0_25_msmt17.pt'

    strong_sort = create_tracker(tracker_type = tracker_type, tracker_config=tracker_config, reid_weights=reid_weights, device=torch.device('cuda:0'), half=True)
    return strong_sort

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