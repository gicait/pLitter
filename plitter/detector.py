import os
import torch

weights = {
    'street': {
        'weights': './models/pLitterStreet_YOLOv5l.pt',
        'url': 'https://github.com/gicait/pLitter/releases/download/StreetTest/pLitterStreet_YOLOv5l.pt'
    },
    'cctv': {
        'weights': './models/pLitterFloat_800x752_to_640x640.pt',
        'url': 'https://github.com/gicait/pLitter/releases/download/v0.1/pLitterFloat_800x752_to_640x640.pt'
    }
}

class detector():

    def __init__(self):
        return None

    def load(self, type='street'):
        if type not in weights.keys():
            raise ValueError('Invalid type. Valid types are: ' + ', '.join(weights.keys()))
        if not os.path.isfile(weights[type]['weights']):
            weights_url = weights[type]['url']
            print('Downloading model from', weights_url)
            torch.hub.download_url_to_file(weights_url, weights[type]['weights'], hash_prefix=None, progress=True)

        return torch.hub.load('ultralytics/yolov5', 'custom', weights[type]['weights'], force_reload=True)