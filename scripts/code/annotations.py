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
                image["width"] = 3840
                image["height"] = 2160
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

    print(data)
    with open(file2, 'w') as outfile:
        json.dump(data, outfile)

# class pLitterAnnots:

#     def requestAnnots():
#         return "True"
    
#     def convertAnnots():
#         return "True"
    
#     def other():
#         return "other"

