import os
import json
import requests
import time
import cv2
import json

class_map = {'debris': 'plastic', 'bottle': 'Plastic bottle', 'styrofoam': 'Styrofoam', 'trash bag': 'Trash bag', 'straw': 'Straw'}

# ------make sure below env vars are set before run----------
root_dir = os.getenv('root_dir', 'project_home')
url = os.getenv('url', None)
dataset_id = os.getenv('dataset_id', None)
key = os.getenv('key', '--secrte-key--')

print(root_dir, url, dataset_id)

if not (url and dataset_id):
    print("need api details to uplaod")
    exit()

image_url = url+'/api/image/'
prediction_url = url+'/api/annotator/predictions'

image_dir = root_dir+'/data'
headers = {"Content-Type": "application/json; charset=utf-8"}

while True:
    images_list = sorted([im for im in os.listdir(image_dir) if im.endswith('.jpg')])
    for image in images_list:
        print(image)
        if image.endswith(('.png', '.jpg')) and os.path.isfile(os.path.join(image_dir,image)):
            if os.path.getsize(os.path.join(image_dir,image)) == 0:
                try:
                    os.remove(os.path.join(image_dir, image))
                    os.remove(os.path.join(image_dir, image.replace('.jpg', '.json')))
                except:
                    pass
                continue
            files = {'image': open(os.path.join(image_dir,image), 'rb')}
            data = {'dataset_id': dataset_id, 'key': key}
            try:
                r = requests.post(image_url, files=files, data=data, timeout=119)
                print(r.status_code)
                if r.status_code in (200, 400):
                    print("image uploaded successfully")
                    r_json = r.json()
                    print(r_json)
                    if 'image_id' in r_json.keys():
                        image_id = r_json['image_id']
                        print(image_id)
                        json_data = json.load(open(os.path.join(image_dir,image.replace('.jpg', '.json')), 'rb'))
                        if len(json_data['preds']) == 0:
                            print('no detections')
                            os.remove(os.path.join(image_dir, image))
                            os.remove(os.path.join(image_dir, image.replace('.jpg', '.json')))
                        else:
                            det_data = {'image_id': image_id, 'key': key, 'detections': []}
                            for det in  json_data['preds']:
                                det_data['detections'].append({
                                    'category': class_map[det['category']] if det['category'] in class_map.keys() else 'plastic',
                                    'isbbox': True,
                                    'bbox': det['bbox'],
                                    'segmentation': det['segmentation']
                                })
                            print(det_data)
                            rr = requests.post(prediction_url, json=det_data, timeout=119)
                            print(rr.status_code, rr.json())
                            if rr.status_code == 200:
                                print('detections uploaded successfully')
                                os.remove(os.path.join(image_dir, image))
                                os.remove(os.path.join(image_dir, image.replace('.jpg', '.json')))
                    else:
                        pass
                else:
                    print("failed to upoad the image")
            except requests.exceptions.ConnectionError as errc:
                print("Error connecting:", errc)
            except requests.exceptions.HTTPError as errh:
                print("Http error:", errh)
            except requests.exceptions.Timeout as errt:
                print("Timeout error:", errt)
            except requests.exceptions.RequestException as err:
                print("Uknown:", err)
    print("sleep for a minute") 
    time.sleep(60)
