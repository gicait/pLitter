import os, sys

root_dir = os.path.dirname(os.path.abspath(__file__))

if os.path.join(root_dir, 'Yolov5_StrongSORT_OSNet') not in sys.path:
    sys.path.append(os.path.join(root_dir, 'Yolov5_StrongSORT_OSNet'))
if os.path.join(root_dir, 'Yolov5_StrongSORT_OSNet/yolov5') not in sys.path:
    sys.path.append(os.path.join(root_dir, 'Yolov5_StrongSORT_OSNet/yolov5'))
if os.path.join(root_dir, 'Yolov5_StrongSORT_OSNet/trackers/strong_sort') not in sys.path:
    sys.path.append(os.path.join(root_dir, 'Yolov5_StrongSORT_OSNet/trackers/strong_sort'))

from trackers.strong_sort.utils.parser import get_config
from trackers.strong_sort.strong_sort import StrongSORT

class Tracker():

    def __init__(self):
        pass

    def load(self, reid_weights, device, half):

        cfg = get_config()
        cfg.merge_from_file(os.path.join(root_dir, 'Yolov5_StrongSORT_OSNet/trackers/strong_sort/configs/strong_sort.yaml'))

        tracker = StrongSORT(
            reid_weights,
            device,
            half,
            max_dist=cfg.STRONGSORT.MAX_DIST,
            max_iou_distance=cfg.STRONGSORT.MAX_IOU_DISTANCE,
            max_age=cfg.STRONGSORT.MAX_AGE,
            max_unmatched_preds=99,
            #max_unmatched_preds=cfg.STRONGSORT.MAX_UNMATCHED_PREDS,
            #n_init=cfg.STRONGSORT.N_INIT,
            n_init=0,
            nn_budget=cfg.STRONGSORT.NN_BUDGET,
            mc_lambda=cfg.STRONGSORT.MC_LAMBDA,
            ema_alpha=cfg.STRONGSORT.EMA_ALPHA,
        )

        tracker.model.warmup()
        return tracker