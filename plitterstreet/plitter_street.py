"""
    The tool to identify and map the plastic litters in the streets using street view data, which are the sequence georefrenced images.
"""

import os, sys
import cv2
import csv, json
from exif import Image

import folium
from folium import plugins
from folium.plugins import HeatMap
from folium.features import ColorLine

from .predict import draw_boxes_on_image

def get_color(val):

    valitudes = {
        0: '#008800',
        1: '#5d8800',
        5: '#7d8800',
        10: '#887600',
        20: '#885800',
        30: '#883f00',
        50: '#883900',
        70: '#882700',
        90: '#881000',
        100: '#880000',
    }
    first = -1
    for valitude in valitudes.keys():
        if first < val <= valitude:
            return valitudes[valitude]
        first = valitude
    return '#FF0000'

icon_circle = folium.plugins.BeautifyIcon(
    icon_shape='circle-dot', 
    border_color='green', 
    border_width=10,
)

icon_bin=folium.Icon(color="blue",icon="trash", prefix='fa')

icon_pile=folium.Icon(color="red",icon="dumpster-fire", prefix='fa')

def convert2decimal(coords, ref):
        decimal_degrees = coords[0] + coords[1] / 60 + coords[2] / 3600
        if ref == "S" or ref == "W":
            decimal_degrees = -decimal_degrees
        return decimal_degrees

class StreetData:
    def __init__(self, path, images_list='', images_json=''):
        self.images_dir = path
        if images_list == '':
            self.images_list = os.path.basename(path)+'.csv'
        else:
            self.images_list = images_list
        if not os.path.isfile(os.path.join(self.images_dir, self.images_list)):
            print('Images list file is invalid. Ignore it if the images file names are in order of GPS track.')
        if images_json == '':
            self.images_json = os.path.basename(path)+'.json'
        else:
            self.images_json = images_list
        if not os.path.isfile(os.path.join(self.images_dir, self.images_json)):
            print('Predictions file is invalid. Ignore it if the images are not predicted and saved.')
        self.images = list()
        self.predictions = list()

    def load_images_from_dir(self):
        # a.sort(key=lambda f: int("".join(filter(str.isdigit, f))))
        self.images = []
        for filename in os.listdir(self.images_dir).sort(key=lambda f: int("".join(filter(str.isdigit, f)))):
                img = cv2.imread(os.path.join(self.images_dir,filename))
                if img is not None:
                    img_exif = Image(open(os.path.join(self.images_dir,filename), 'rb'))
                    if img_exif.has_exif:
                        if 'gps_longitude' in img_exif.list_all() and 'gps_latitude' in img_exif.list_all():
                            image_dict = dict()
                            image_dict['name'] = filename
                            try:
                                image_dict['latitude'] = convert2decimal(img_exif.gps_latitude, img_exif.gps_latitude_ref)
                                image_dict['longitude'] = convert2decimal(img_exif.gps_longitude, img_exif.gps_longitude_ref)
                                self.images.append(image_dict)
                            except AttributeError:
                                print('GPS Coordinates not found in', filename)
                    else:
                        print('No EXIF information in', filename)
        print(len(self.images), 'images are found in the directory.')

    def load_images_from_list(self):
        self.images = []
        if os.path.isfile(os.path.join(self.images_dir, self.images_list)):
            with open(os.path.join(self.images_dir, self.images_list), 'r') as csvf:
                reader = csv.DictReader(csvf)
                for row in reader:
                    filename = row['Name']
                    if os.path.isfile(os.path.join(self.images_dir, filename)):
                        img = cv2.imread(os.path.join(self.images_dir,filename))
                        if img is not None:
                            img_exif = Image(open(os.path.join(self.images_dir,filename), 'rb'))
                            if img_exif.has_exif:
                                if 'gps_longitude' in img_exif.list_all() and 'gps_latitude' in img_exif.list_all():
                                    image_dict = dict()
                                    image_dict['name'] = filename
                                    try:
                                        image_dict['latitude'] = convert2decimal(img_exif.gps_latitude, img_exif.gps_latitude_ref)
                                        image_dict['longitude'] = convert2decimal(img_exif.gps_longitude, img_exif.gps_longitude_ref)
                                        self.images.append(image_dict)
                                    except AttributeError:
                                        print('GPS Coordinates not found in', filename)
                            else:
                                print('No EXIF information in', filename)
        else:
            print('File not found with images list, we must need it keep the images in sequennce order, otherwise hotline would be zigzag and not in order. If you dont have it prepare a CSV file in side the images folder as "folder_name.csv", and list the images filenames in it in the order.')
            missing_images = []
            for filename in os.listdir(self.images_dir):
                img = cv2.imread(os.path.join(self.images_dir,filename))
                if img is not None:
                    img_exif = Image(open(os.path.join(self.images_dir,filename), 'rb'))
                    if img_exif.has_exif:
                        if 'gps_longitude' in img_exif.list_all() and 'gps_latitude' in img_exif.list_all():
                            image_dict = dict()
                            image_dict['name'] = filename
                            try:
                                image_dict['latitude'] = convert2decimal(img_exif.gps_latitude, img_exif.gps_latitude_ref)
                                image_dict['longitude'] = convert2decimal(img_exif.gps_longitude, img_exif.gps_longitude_ref)
                                missing_images.append(image_dict)
                            except AttributeError:
                                print('GPS Coordinates not found in', filename)
                    else:
                        print('No EXIF information in', filename)
            print(len(missing_images), 'images have georefernce and are missing in the list.')

    def predict_on_images(self, predictor, min_score_thr=0.5, dst_path=''):
        dst_path = self.images_dir
        if not os.path.isdir(os.path.join(dst_path, 'predictions')):
            os.makedirs(os.path.join(dst_path, 'predictions'))
        for image in self.images:
            frame = cv2.imread(os.path.join(self.images_dir, image['name']))
            output = predictor.predict(frame)
            classes = output['detection_classes_as_text'].numpy()[0]
            scores = output['detection_scores'].numpy()[0]
            boxes = output['detection_boxes'].numpy()[0]
            result = draw_boxes_on_image(image=frame, boxes=boxes, classes=classes, scores=scores, use_normalized_coordinates=True, min_score_thresh=0.2)
            cv2.imwrite(os.path.join(os.path.join(dst_path, 'predictions'), image['name']), result)
            # image['predictions'] = []
            image['Plastic'] = 0
            image['Pile'] = 0
            image['Trash bin'] = 0
            image['Face mask'] = 0
            for i in range(len(boxes)):
                if scores[i] >= min_score_thr:
                    image[classes[i].decode()] += 1
                    item = {'image': image['name'], 'class': classes[i].decode(), 'box': [round(float(boxes[i].tolist()[1]), 2), round(float(boxes[i].tolist()[0]), 2), round(float(boxes[i].tolist()[3]), 2), round(float(boxes[i].tolist()[2]), 2)], 'score': round(float(scores[i]), 2)}
                    self.predictions.append(item)
    
    def load_data_from_json(self):
        with open(self.images_json) as jsf:
            data = json.load(jsf)
            self.images = data['images']
            self.predictions = data['predictions']
    
    def save(self, dst_path=''):
        folder_name = os.path.basename(self.images_dir)
        data = dict()
        data[folder_name] = self.images
        if dst_path=='':
            json.dump(data, open(os.path.join(self.images_dir, folder_name+'.json'), 'w'))
        else:
            json.dump(data, open(os.path.join(dst_path, folder_name+'.json'), 'w'))

    def draw_street_on_map(self, m):
        points = self.images
        if not type(m) == folium.folium.Map:
            m = folium.Map(tiles="OpenStreetMap", prefer_canvas=True)

            images = folium.FeatureGroup(name='Images',overlay=True)
            hotline = folium.FeatureGroup(name='Hot line',overlay=True)
            heatmap = folium.FeatureGroup(name='Heat map',overlay=True)
            piles = folium.FeatureGroup(name='Piles',overlay=True)
            trashbins = folium.FeatureGroup(name='Trash bins',overlay=True)

            images.add_to(m)
            hotline.add_to(m)
            heatmap.add_to(m)
            piles.add_to(m)
            trashbins.add_to(m)

            folium.LayerControl().add_to(m) 

        heat_data = []
        max_count = 0
        for k in range(len(points)):
            if points[k]['Trash bin']:
                folium.Marker([float(points[k]['latitude']), float(points[k]['longitude'])], icon=icon_bin).add_to(trashbins)
            if points[k]['Pile']:
                folium.Marker([float(points[k]['latitude']), float(points[k]['longitude'])], icon=icon_pile).add_to(piles)
            folium.CircleMarker([float(points[k]['latitude']), float(points[k]['longitude'])], radius=.1, popup="<i>"+points[k]['name']+"</i>", tooltip=points[k]['name'], icon=icon_circle).add_to(images)
            if k < len(points)-1:
                p1_count = points[k]['Plastic']+points[k]['Face mask']+points[k]['Pile']*100
                p2_count = points[k+1]['Plastic']+points[k+1]['Face mask']+points[k+1]['Pile']*100
                avg_count = (p1_count+p2_count)//2
                if max_count < avg_count:
                    max_count = avg_count
                color = get_color((p1_count+p2_count)//2)
                heat_data.append([points[k]['latitude'], points[k]['longitude'], avg_count])
                ColorLine(
                    [
                        [points[k]['latitude'], points[k]['longitude']],
                        [points[k+1]['latitude'], points[k+1]['longitude']],
                    ],
                    colors=[1],
                    colormap=[color, color],
                    weight=3,
                ).add_to(hotline)
        HeatMap(heat_data, radius = 10, min_opacity = 0.1, max_val = max_count, gradient={.0: 'green', .1: 'yellow', .5: 'red', .9: 'blue'}).add_to(heatmap)
        m.fit_bounds(m.get_bounds())
        return m