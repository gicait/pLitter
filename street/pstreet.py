import os

class pStreet:
    def __init__(self, path):
        if not os.path.isdir(path):
            return None
        self.images = []
        self.videos = []

    def load(self):
        for fl in os.listdir(path):
            if fl is image:
                exif gps
                if gps:
                    self.images.append(fl)
                else:
                    ignore
                    they can check plitter website
                    
            elif fl is video(path):
                find gpx
                if not gpx:
                    ignore
                else:
                    self.videos.append(fl)

    def predict(self, type, weights):
        if type is yolov5:
            model = yolov5(weights)
        elif type if tf:
            model = tf.load(weights)
