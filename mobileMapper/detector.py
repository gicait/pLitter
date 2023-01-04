import os
import torch

weights = '../models/pLitterStreet_YOLOv5l.pt'
weights_url = 'https://github.com/gicait/pLitter/releases/download/StreetTest/pLitterStreet_YOLOv5l.pt'

if not os.path.isfile(weights):
    print('Downloading model from', weights)
    torch.hub.download_url_to_file(weights_url, weights, hash_prefix=None, progress=True)

model = torch.hub.load('ultralytics/yolov5', 'custom', weights, force_reload=True)