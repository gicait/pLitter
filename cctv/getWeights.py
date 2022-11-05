from genericpath import isfile
import os
home = os.path.expanduser("~") 
cctv_path = os.path.dirname(os.path.realpath(__file__))
root_path = os.path.dirname(cctv_path)
print(root_path)
weights_path = os.path.join(root_path, 'models')
os.makedirs(weights_path, exist_ok=True)
import requests
import yaml

def download_file(url):
    local_filename = '.'+url.split('/')[-1]
    # NOTE the stream=True parameter below
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(os.path.join(weights_path, local_filename), 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                # If you have chunk encoded response uncomment if
                # and set chunk_size parameter to None.
                #if chunk:
                f.write(chunk)
    return local_filename, True

weights_url = None
with open(os.path.join(cctv_path, 'conf.yaml'), 'r') as inf:
    data = yaml.safe_load(inf)
    print(data)
    if 'new_weights' in data.keys():
        if data['new_weights']:
            weights_url = data['weights_url']
    print(weights_url)
if weights_url:
    local_filename = weights_url.split('/')[-1]
    if not os.path.isfile(os.path.join(weights_path, local_filename)):
        updated = False
        while updated == False:
            try:
                return_weights_file, updated = download_file(weights_url)
                if updated:
                    os.rename(os.path.join(weights_path, return_weights_file), os.path.join(weights_path, return_weights_file[1:]))
            except:
                pass