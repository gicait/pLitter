import os
import json
#import base64
import requests
import time
import yaml
import sqlite3

home = os.path.expanduser("~")

# get address
with open(os.path.join(home, '.cctv'), 'r') as stream:
    data = yaml.safe_load(stream)
url = data['url']
dataset_id = int(data['id'])

image_url = url+'/api/image/'
print(image_url)

image_dir = '/home/cctv/plitter/data'
headers = {"Content-Type": "application/json; charset=utf-8"}

debris_dbpath = '/home/cctv/plitter/db/debris.db' # change this
images_dbpath = '/home/cctv/plitter/db/images.db'

conn = sqlite3.connect(images_dbpath, isolation_level=None)
cur = conn.cursor()

while True:
    #time.sleep(10)
    cur.execute("""SELECT im_name FROM images WHERE uploaded=?""", (False,))
    for row in cur.fetchall():
    #for image in sorted(os.listdir(image_dir)):
        image = row[0]
        print(image)
        #continue
        if image.endswith(('.png', '.jpg')) and os.path.isfile(os.path.join(image_dir,image)):
            print(image)
            files = {'image': open(os.path.join(image_dir,image), 'rb')}
            data = {'dataset_id': dataset_id}
            try:
                r = requests.post(image_url, files=files, data=data, timeout=119)
                print(r.status_code)
                if r.status_code in (200, 400):
                    pass
                    cur.execute("""UPDATE images SET uploaded=? WHERE im_name=?""", (True, image))
                    #os.remove(image_dir+image)
            except requests.exceptions.ConnectionError as errc:
                print("Error connecting:", errc)
            except requests.exceptions.HTTPError as errh:
                print("Http error:", errh)
            except requests.exceptions.Timeout as errt:
                print("Timeout error:", errt)
            except requests.exceptions.RequestException as err:
                print("Uknown:", err)
    print("sleeping")
    time.sleep(90)
    #time.sleep(90)
