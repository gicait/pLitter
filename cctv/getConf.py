import os
home = os.path.expanduser("~") 
cctv_path = os.path.dirname(os.path.realpath(__file__))
import requests
import yaml

# get address
with open(os.path.join(home, '.cctv'), 'r') as stream:
    data = yaml.safe_load(stream)
    print(data)

url = data['url']
id = str(data['id'])

conf = {'frame_width': 1920, 'frame_height': 1080, 'silce_width': 640, 'slice_height': 640, 'interval': 20, 'send_empty': True, 'weights_url': '', 'new_weights': False, 'pull': False, 'images_prefix': ''}

with open(os.path.join(cctv_path, 'conf.yaml'), 'r') as inf:
    data = yaml.safe_load(inf)
    print(data)
    if type(data) == dict():
        for k, v in data:
            if k in conf.keys():
                conf[k] = v

try:
    res = requests.get(url+'/api/dataset/'+id+'/config', timeout=30)
    if res.status_code == 200:
        re = res.json()
        print(re, type(re))
        for k,v in re.items():
            if k in conf.keys():
                if k == 'weights_url':
                    if conf[k] == v:
                        conf['new_weights'] = False
                    else:
                        conf[k] = v
                        conf['new_weights'] = True
                else:
                    conf[k] = v

    with open(os.path.join(cctv_path, 'conf.yaml'), 'w') as outf:
        yaml.dump(conf, outf)
except:
    pass
