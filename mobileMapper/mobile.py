"""
    The tool to identify and map the plastic litters in the streets using street view data, which are the sequence georefrenced images.
"""

import os, sys, re, glob
import csv, json
from datetime import datetime
import cv2
import gpxpy
from exif import Image
import pandas as pd

"""

input: 
    path to the directory of images/videos
    images should must have GPS location in the EXIF data
    videos should have GPX/CSV file with the same name

output: json file with the following structure

geojson = {
    "type": "FeatureCollection"
    "features": [
        {
            "type": "Feature",
            "properties": {
                "file_name": "image.jpg",
                "plastic": 1,
                "pile": 1,
                "face mask": 1,
                "trash bin": 1,
                "boxes": [
                    [100, 100, 10, 20], 
                    [120, 170, 30, 10]
                ]
            },
            "geometry": {
                "type": "Point",
                "Coordinates": [x,y]
            }
        }
    ] 
}

csv = [
    ["file_name", "cts", "lat", "long", "plastic", "pile", "face mask", "trash bin", "boxes"],
    ["image.jpg", 0, x, y, 1, 1, 1, 1, "[100, 100, 10, 20], [120, 170, 30, 10]"]
]
"""
def convert2decimal(coords, ref):
    decimal_degrees = coords[0] + coords[1] / 60 + coords[2] / 3600
    if ref == "S" or ref == "W":
        decimal_degrees = -decimal_degrees
    return decimal_degrees
    
class pImage:
    
    def __init__(self, file_name, lat=None, lon=None, preds=None):
        
        self.file_name = file_name
        self.latitude = lat
        self.longitude = lon
        self.predictions = preds
        
class pVideo:

    def __init__(self, file_name, gpx_df=None, preds=None):
        
        self.file_name = file_name
        self.gpx = gpx_df
        self.predictions = preds

class pTrack:

    def __init__(self, directory):
        if not os.path.isdir(directory):
            raise Exception("Path not found")

        self.directory = directory
        self.images = list()
        self.videos = list()
        self.predictions = list()
        
    def load(self):
        filenames = os.listdir(self.directory)
        images = list(filter(lambda x: x.lower().endswith(('.png', '.jpg', '.jpeg')), filenames))
        videos = list(filter(lambda x: x.lower().endswith(('.mp4', '.mkv', '.avi')), filenames))
        images.sort(key = lambda f: int(re.sub('\D', '', f)))
        videos.sort(key = lambda f: int(re.sub('\D', '', f)))
        
        for image in images:
            try:
                img_exif = Image(open(os.path.join(self.directory, image), 'rb'))
                if img_exif.has_exif:
                    if 'gps_longitude' in img_exif.list_all() and 'gps_latitude' in img_exif.list_all():
                        pimage = pImage(image)
                        try:
                            pimage.latitude = convert2decimal(img_exif.gps_latitude, img_exif.gps_latitude_ref)
                            pimage.longitude = convert2decimal(img_exif.gps_longitude, img_exif.gps_longitude_ref)
                            self.images.append(pimage)
                        except AttributeError:
                            print('error parsing GPS Coordinates in', image)
                else:
                    print('No EXIF information in', image)
            except:
                print(image, "some error may be, if you are using it for just ti check to predictions, visit plitter.org/demo and drop the images there.")

        print(len(self.images), 'images are found in the directory.')

        for video in videos:
            gpx_path = os.path.join(self.directory, os.path.splitext(video)[0]+'.gpx')
            if os.path.isfile(gpx_path):
                print('gpx file found for', video)
                try:
                    with open(gpx_path) as f:
                        gpx = gpxpy.parse(f)
                    prev_time = None
                    points = []
                    for segment in gpx.tracks[0].segments:
                        for p in segment.points:
                            points.append({
                                'cts': (p.time - prev_time).total_seconds() if prev_time else 0, 
                                'time': p.time,
                                'latitude': p.latitude,
                                'longitude': p.longitude,
                                'elevation': p.elevation,
                            })
                            if prev_time is None:
                                prev_time = p.time
                    df = pd.DataFrame.from_records(points)
                    pvideo = pVideo(video, df)
                    self.videos.append(pvideo)
                except:
                    print(video, "Errors, check if video file and GPX file are valid. If you are intend to check the predictions, visit plitter.org/demo and drop the images there.")
            else:
                print('gpx file not found for', video)

        print(len(self.videos), 'videos are found in the directory.')

    def detectImages(self, model):
        print('Detecting plastic litters in images')
        for image in self.images:
            print(image.file_name)
            img = cv2.imread(os.path.join(self.directory, image.file_name))
            preds = model(img, size=1280)
            class_ids = preds.xyxy[0].cpu().numpy()[:, 5]
            classes = [preds.names[cls] for cls in class_ids]
            scores = preds.xyxy[0].cpu().numpy()[:, 4]
            boxes = preds.xyxy[0].cpu().numpy()[:,:4]
            image.predictions = {'category_ids': class_ids, 'classes': classes, 'boxes': boxes, 'scores': scores}

    def detectVideos(self, model):
        print('Detecting plastic litters in videos')
        for video in self.videos:
            print(video.file_name)
            vidcap = cv2.VideoCapture(os.path.join(self.directory, video.file_name))
            while vidcap.isOpened():
                success, image = vidcap.read()
                if success:
                    preds = model(image, size=1280)
                    class_ids = preds.xyxy[0].cpu().numpy()[:, 5]
                    classes = [preds.names[cls] for cls in class_ids]
                    scores = preds.xyxy[0].cpu().numpy()[:, 4]
                    boxes = preds.xyxy[0].cpu().numpy()[:,:4]
                    video.predictions.append({'frame_cts': vidcap.get(cv2.CAP_PROP_POS_MSEC)*1000, 'category_ids': class_ids, 'classes': classes, 'boxes': boxes, 'scores': scores})

    def detect(self, model):
        self.detectImages(model)
        self.detectVideos(model)

    def export(self, output_file):
        geojson = {
            "type": "FeatureCollection",
            "features": []
        }

        for image in self.images:
            feature = {
                "type": "Feature",
                "properties": {
                    "file_name": image.file_name,
                    "plastic": [],
                    "pile": [],
                    "face mask": [],
                    "trash bin": [],
                },
                "geometry": {
                    "type": "LineString",
                    "Coordinates": [image.latitude, image.longitude]
                }
            }
            for i in range(len(image.predictions['classes'])):
                if image.predictions['scores'][i] > 0.4:
                    feature['properties'][image.predictions['classes'][i]].append({
                        "box": image.predictions['boxes'][i].tolist(),
                        "score": image.predictions['scores'][i].tolist()
                    })
 
            geojson['features'].append(feature)

        for video in self.videos:
            feature = {
                "type": "Feature",
                "properties": {
                    "file_name": video.file_name,
                    "indexes": ['lon', 'lat', 'cts', 'count', 'plastic', 'pile', 'face mask', 'trash bin'],
                    "track": []
                },
            }

            for i in range(len(video.predictions)):
                frame_cts = video.predictions[i]['frame_cts']
                near_gpx = video.gpx.iloc[(video.gpx['cts']-frame_cts).abs().argsort()[0]]
                track_point = {'lon': near_gpx.longitude, 'lat': near_gpx.latitude, 'cts': near_gpx.cts, 'count': 0, 'plastic': [], 'pile': [], 'face mask': [], 'trash bin': []}
                for j in range(len(video.predictions[i]['classes'])):
                    if video.predictions[i]['scores'][j] > 0.4:
                        track_point['count'] += 1
                        track_point[video.predictions[i]['classes'][j]].append({
                            "box": video.predictions[i]['boxes'][j].tolist(),
                            "score": video.predictions[i]['scores'][j].tolist()
                        })                
                feature['properties']['track'].append(track_point)
            geojson['features'].append(feature)

        with open(output_file, 'w') as f:
            json.dump(geojson, f)