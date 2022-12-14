import os

root_path = '/home/cctv/plitter' #change root_path

images = os.listdir(root_path+'/data')

if len(images) > 150000:
    for im in sorted(images)[0:10000]:
        os.remove(root_path+'/data/'+im)
else:
    print("not ready for cleaning")
