import os
import json
#import base64
import requests
import time

image_url = 'http://*********/api/image/'
image_dir = '******************'
headers = {"Content-Type": "application/json; charset=utf-8"}

while True:
    time.sleep(10)
    for image in sorted(os.listdir(image_dir)):
        if image.endswith(('.png', '.jpg')):
            print(image)
            files = {'image': open(image_dir+image, 'rb')}
            data = {'dataset_id': 13}
            try:
                r = requests.post(image_url, files=files, data=data, timeout=119)
                print(r.status_code)
                if r.status_code in (200, 400):
                    pass
                    #os.remove(image_dir+image)
            except requests.exceptions.ConnectionError as errc:
                print("Error connecting:", errc)
            except requests.exceptions.HTTPError as errh:
                print("Http error:", errh)
            except requests.exceptions.Timeout as errt:
                print("Timeout error:", errt)
            except requests.exceptions.RequestException as err:
                print("Uknown:", err)
    time.sleep(90)
