import os, json
import requests

# res = request.get('dataset_id')

# write to yml

images = sorted(os.listdir('preds'))
if len(images) > 4:
    for im in images[:-4]:
        res = requests.get('http://cctv.plitter.org/api/image/13/'+im)
        if res.status_code == 404:
            pass
            #upload again
        else:
            print(res.json())
            os.remove('preds/'+im)


def get_slice_bboxes(image_height=1280, image_width=1920, slice_height=840, slice_width=720, overlap_height_ratio=0.1, overlap_width_ratio=0.1):
    
    slice_bboxes = []
    y_max = y_min = 0
    y_overlap = int(overlap_height_ratio * slice_height)
    x_overlap = int(overlap_width_ratio * slice_width)
    while y_max < image_height:
        x_min = x_max = 0
        y_max = y_min + slice_height
        while x_max < image_width:
            x_max = x_min + slice_width
            if y_max > image_height or x_max > image_width:
                xmax = min(image_width, x_max)
                ymax = min(image_height, y_max)
                xmin = max(0, xmax - slice_width)
                ymin = max(0, ymax - slice_height)
                slice_bboxes.append([xmin, ymin, xmax, ymax])
            else:
                slice_bboxes.append([x_min, y_min, x_max, y_max])
            x_min = x_max - x_overlap
        y_min = y_max - y_overlap
    return slice_bboxes