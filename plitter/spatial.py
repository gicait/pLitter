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
import pickle
import torch

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
                "coordinates": [x,y]
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
    
    def __init__(self, file_name, lat=None, lon=None, preds=[]):
        
        self.file_name = file_name
        self.latitude = lat
        self.longitude = lon
        self.predictions = preds
        
class pVideo:

    def __init__(self, file_name, gpx_df=None, preds=[]):
        
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
        self.names = dict()
        
    def load(self, load_pkl=False):
        filenames = os.listdir(self.directory)
        images = list(filter(lambda x: x.lower().endswith(('.png', '.jpg', '.jpeg')), filenames))
        videos = list(filter(lambda x: x.lower().endswith(('.mp4', '.mkv', '.avi')), filenames))

        # sort the images and videos by the alphanumeric order in the file name
        images.sort(key = lambda f: int(re.sub('\D', '', f) if re.sub('\D', '', f) else 0))
        videos.sort(key = lambda f: int(re.sub('\D', '', f) if re.sub('\D', '', f) else 0))
        
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
                            print('error parsing GPS coordinates in', image)
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
                    if load_pkl and os.path.isfile(os.path.join(self.directory, video+'.pkl')):
                        pvideo = pickle.load(open(os.path.join(self.directory, video+'.pkl'), 'rb'))
                    else:
                        pvideo = pVideo(video, df)
                    self.videos.append(pvideo)
                except:
                    print(video, "Errors, check if video file and GPX file are valid. If you are intend to check the predictions, visit plitter.org/demo and drop the images there.")
            else:
                print('gpx file not found for', video)

        print(len(self.videos), 'videos are found in the directory.')

    def detectImages(self, model):
        if self.names == dict():
            self.names = model.names
        print('Detecting plastic litters in images')
        for i in range(len(self.images)):
            print(self.images[i].file_name)
            img = cv2.imread(os.path.join(self.directory, self.images[i].file_name))
            preds = model(img, size=1280)
            class_ids = preds.xyxy[0].cpu().numpy()[:, 5]
            classes = [preds.names[cls] for cls in class_ids]
            scores = preds.xyxy[0].cpu().numpy()[:, 4]
            boxes = preds.xyxy[0].cpu().numpy()[:,:4]
            self.images[i].predictions = {'category_ids': class_ids.tolist(), 'classes': classes, 'boxes': boxes.tolist(), 'scores': scores.tolist()}

    @torch.no_grad()
    def detectVideos(self, model, tracker=None, skip_frames=0):
        if self.names == dict():
            self.names = model.names
        print('Detecting plastic litters in videos')
        for i in range(len(self.videos)):
            print(self.videos[i].file_name, self.videos[i].predictions)
            vidcap = cv2.VideoCapture(os.path.join(self.directory, self.videos[i].file_name))
            fps = vidcap.get(cv2.CAP_PROP_FPS)
            frame_count = vidcap.get(cv2.CAP_PROP_FRAME_COUNT)
            duration = frame_count/fps
            last_pos = 0.0
            print('fps:', fps, 'frame_count:', frame_count, 'duration:', duration)
            skipped_frames = 0
            if tracker is None:
                while vidcap.isOpened():
                    success, image = vidcap.read()
                    if skip_frames > 0:
                        if skipped_frames%skip_frames != 0:
                            skipped_frames += 1
                            print('skipped frame', skipped_frames)
                            continue
                    skipped_frames += 1
                    if success:
                        preds = model(image, size=1280)
                        class_ids = preds.xyxy[0].cpu().numpy()[:, 5]
                        classes = [preds.names[cls] for cls in class_ids]
                        scores = preds.xyxy[0].cpu().numpy()[:, 4]
                        boxes = preds.xyxy[0].cpu().numpy()[:,:4]
                        rec = {'frame_cts': vidcap.get(cv2.CAP_PROP_POS_MSEC)*0.001, 'category_ids': class_ids.tolist(), 'classes': classes, 'boxes': boxes.tolist(), 'scores': scores.tolist()}
                        self.videos[i].predictions.append(rec)
                        print(rec)

                    if vidcap.get(cv2.CAP_PROP_POS_MSEC) != 0.0:
                        last_pos = vidcap.get(cv2.CAP_PROP_POS_MSEC)
                    else:
                        last_pos += 1000/fps

                    print(last_pos, duration)
                    if duration*1000 <= last_pos:
                        print('video', self.videos[i].file_name, 'is finished')
                        break
            else:
                prev_frame = None
                curr_frame = None
                while vidcap.isOpened():
                    success, image = vidcap.read()
                    if skip_frames > 0:
                        if skipped_frames%skip_frames != 0:
                            skipped_frames += 1
                            print('skipped frame', skipped_frames)
                            continue
                    skipped_frames += 1
                    if success:
                        preds = model(image, size=1280)
                        if prev_frame is not None and curr_frame is not None:
                            tracker.tracker.camera_update(prev_frame, curr_frame)
                        if len(preds.xyxy[0].cpu()) > 0:
                            print(preds.xyxy[0].cpu())
                            outputs = tracker.update(preds.xyxy[0].cpu(), image)
                            print(outputs)
                            if len(outputs):
                                class_ids = outputs[:, 5].astype(int)
                                track_ids = outputs[:, 4]
                                classes = [preds.names[int(cls)] for cls in class_ids]
                                scores = [float(f) for f in outputs[:, 6]]
                                boxes = outputs[:,:4]
                                # print(class_ids, track_ids, classes, scores, boxes)
                                rec = {'frame_cts': vidcap.get(cv2.CAP_PROP_POS_MSEC)*0.001, 'category_ids': class_ids.tolist(), 'classes': classes, 'boxes': boxes.tolist(), 'scores': scores}
                                self.videos[i].predictions.append(rec)
                                print(rec)

                    if vidcap.get(cv2.CAP_PROP_POS_MSEC) != 0.0:
                        last_pos = vidcap.get(cv2.CAP_PROP_POS_MSEC)
                    else:
                        last_pos += 1000/fps
                    prev_frame = curr_frame

                    print(last_pos, duration)
                    if duration*1000 <= last_pos:
                        print('video', self.videos[i].file_name, 'is finished')
                        break

            vidcap.release()
            with open(os.path.join(self.directory, self.videos[i].file_name+'.pkl'), 'wb') as f:
                pickle.dump(self.videos[i], f)

    def detect(self, model, tracker=None, skip_frames=0):
        self.names = model.names
        self.detectImages(model)
        self.detectVideos(model, tracker=tracker, skip_frames=skip_frames)

    def export(self, output_file, with_predictions=False, html=False):
        if with_predictions:
            geojson = {
                "type": "FeatureCollection",
                "features": []
            }

            for image in self.images:
                feature = {
                    "type": "Feature",
                    "properties": {
                        "file_name": image.file_name,
                        "count": 0,
                    },
                    "geometry": {
                        "type": "Point",
                        "coordinates": [round(image.longitude, 6), round(image.latitude, 6)]
                    }
                }
                for name in self.names.values():
                    feature['properties'].update({name: []})
                
                for i in range(len(image.predictions['classes'])):
                    if image.predictions['scores'][i] > 0.4:
                        if image.predictions['classes'][i] != 'Trash bin':
                            feature['properties']['count'] += 1
                        feature['properties'][image.predictions['classes'][i]].append({
                            "box": [int(x) for x in image.predictions['boxes'][i]],
                            "score": round(image.predictions['scores'][i], 2)
                        })
    
                geojson['features'].append(feature)

            for video in self.videos:
                feature = {
                    "type": "Feature",
                    "properties": {
                        "file_name": video.file_name,
                        "indexes": ['lon', 'lat', 'cts', 'count'],
                        "track": []
                    },
                    "geometry": {
                        "type": "LineString",
                        "coordinates": []
                    }
                }
                feature['properties']['indexes'].extend(self.names.values())

                for i in range(len(video.predictions)):
                    frame_cts = video.predictions[i]['frame_cts']
                    near_gpx = video.gpx.iloc[(video.gpx['cts']-frame_cts).abs().argsort()[0]]
                    track_point = {'lon': round(near_gpx.longitude, 6), 'lat': round(near_gpx.latitude, 6), 'cts': round(near_gpx.cts, 3), 'count': 0}
                    track_point.update({name: [] for name in self.names.values()})
                    for j in range(len(video.predictions[i]['classes'])):
                        if video.predictions[i]['scores'][j] > 0.4:
                            if video.predictions[i]['classes'][j] != 'Trash bin':
                                track_point['count'] += 1
                            track_point[video.predictions[i]['classes'][j]].append({
                                # convert list of floats to list of integers
                                "box": [int(x) for x in video.predictions[i]['boxes'][j]],
                                "score": round(video.predictions[i]['scores'][j], 2)
                            })                
                    feature['geometry']['coordinates'].append([round(near_gpx.longitude, 6), round(near_gpx.latitude, 6)])
                    feature['properties']['track'].append(list(track_point.values()))
                geojson['features'].append(feature)

            with open(output_file, 'w') as f:
                json.dump(geojson, f)
        else:
            geojson = {
                "type": "FeatureCollection",
                "features": []
            }

            for image in self.images:
                feature = {
                    "type": "Feature",
                    "properties": {
                        "file_name": image.file_name,
                        "count": 0,
                    },
                    "geometry": {
                        "type": "Point",
                        "coordinates": [round(image.longitude, 6), round(image.latitude, 6)]
                    }
                }
                for name in self.names.values():
                    feature['properties'].update({name: 0})
                
                for i in range(len(image.predictions['classes'])):
                    if image.predictions['scores'][i] > 0.4:
                        if image.predictions['classes'][i] != 'Trash bin':
                            feature['properties']['count'] += 1
                        feature['properties'][image.predictions['classes'][i]] += 1
    
                geojson['features'].append(feature)

            for video in self.videos:
                feature = {
                    "type": "Feature",
                    "properties": {
                        "file_name": video.file_name,
                        "indexes": ['lon', 'lat', 'cts', 'count'],
                        "track": []
                    },
                    "geometry": {
                        "type": "LineString",
                        "coordinates": []
                    }
                }
                feature['properties']['indexes'].extend(self.names.values())

                for i in range(len(video.predictions)):
                    frame_cts = video.predictions[i]['frame_cts']
                    near_gpx = video.gpx.iloc[(video.gpx['cts']-frame_cts).abs().argsort()[0]]
                    track_point = {'lon': round(near_gpx.longitude, 6), 'lat': round(near_gpx.latitude, 6), 'cts': round(near_gpx.cts, 3), 'count': 0}
                    track_point.update({name: 0 for name in self.names.values()})
                    for j in range(len(video.predictions[i]['classes'])):
                        if video.predictions[i]['scores'][j] > 0.4:
                            if video.predictions[i]['classes'][j] != 'Trash bin':
                                track_point['count'] += 1
                            track_point[video.predictions[i]['classes'][j]] += 1
                    feature['geometry']['coordinates'].append([round(near_gpx.longitude, 6), round(near_gpx.latitude, 6)])
                    feature['properties']['track'].append(list(track_point.values()))
                geojson['features'].append(feature)

            with open(output_file, 'w') as f:
                json.dump(geojson, f)
        if html:
            # TODO: add html output, use a templte to poen the geojson file
            pass
