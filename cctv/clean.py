import os

images = os.listdir('/home/cctv/plitter/data')
if len(images) > 10000:
    for im in sorted(images)[0:10000]:
        os.remove('/home/cctv/plitter/data/'+im)
else:
    print("not ready for cleaning")
