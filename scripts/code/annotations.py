'''
manages annotations
'''
import os
import csv
import json


def csvtojson(file1, file2):
    data = {}
    images = []
    categories = []
    annotations = []

    new_image_id = 1
    new_category_id = 1
    new_annotation_id = 1
    with open(file1, "r") as csvfile:
        csvreader = csv.reader(csvfile)
        for row in csvreader:
            image = next((item for item in images if item["file_name"] == row[0]), None)
            if not image:
                image = {}
                image["id"] = new_image_id+1
                image["width"] = 1280
                image["height"] = 720
                image["file_name"] = row[0]
                images.append(image)
                new_image_id += 1

            category = next((item for item in categories if item["name"] == row[1]), None)                
            if not category:
                category = {}
                category["id"] = new_category_id
                category["name"] = row[1]
                category["supercategory"] = "Plastic"
                categories.append(category)
                new_category_id += 1
            
            image_id = image["id"]
            category_id = category["id"]

            xmin, ymin, xmax, ymax = float(row[2]), float(row[3]), float(row[4]), float(row[5])
            annotation= {}
            annotation["id"] = new_annotation_id
            annotation["image_id"] = image_id
            annotation["category_id"] = category_id
            annot_x1, annot_y1 = image["width"]*xmin, image["height"]*ymin
            annot_x2, annot_y2 = image["width"]*xmax, image["height"]*ymax
            annot_width = annot_x2 - annot_x1
            annot_height = annot_y2 - annot_y1 
            annotation["segmentation"] = [[annot_x1, annot_y1, annot_x2, annot_y1, annot_x2, annot_y2, annot_x1, annot_y2]]
            annotation["bbox"] = [annot_x1, annot_y1, annot_width, annot_height]
            annotation["isbbox"] = True
            annotations.append(annotation)
            new_annotation_id += 1

    data["images"] = images
    data["categories"] = categories
    data["annotations"] = annotations

    # print(data)
    with open(file2, 'w') as outfile:
        json.dump(data, outfile)
    outfile.close()


def jsontocsv(file1, file2, image_width, image_height):
    with open(file1, "r") as jsonfile:
        json_data = json.load(jsonfile)
        rows = []
        images = json_data['images']
        categories = json_data['categories']
        annotations = json_data['annotations']
        for annotation in annotations:
            row = []
            segmentation = annotation['segmentation'][0]
            xmin = segmentation[0]/image_width
            ymin = segmentation[1]/image_height
            xmax = segmentation[2]/image_width
            ymax = segmentation[5]/image_height

            image_id = annotation['image_id']
            image_name = next((image['file_name'] for image in images if image["id"] == image_id), None)
            category_id = annotation['category_id']
            category_name = next((category['name'] for category in categories if category['id'] == category_id), None)
            row.append(image_name)
            row.append(category_name)
            row.append(xmin)
            row.append(ymin)
            row.append(xmax)
            row.append(ymax)
            rows.append(row)
            
        with open(file2, 'w') as csvfile:
            csvwriter = csv.writer(csvfile)
            for row in rows:
                csvwriter.writerow(row)
        csvfile.close()



            # GX044613 5.jpg,Plastic,0.1770421713590622,0.5861731171607971,0.20449234545230865,0.6124027371406555



# class pLitterAnnots:

#     def requestAnnots():
#         return "True"
    
#     def convertAnnots():
#         return "True"
    
#     def other():
#         return "other"


