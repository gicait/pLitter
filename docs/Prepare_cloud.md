This document explains the minimal cloud API needed to upload the images and detections from pLitterCCTVs. The overall working pipeline of monitoring floating plastic with pLitterCCTVs is showing in the below diagram.

To store the information colelcted by the cameras it requires four collections in the database,

The enity relationship diagram of the database is given below.

    1. Datasets => Each Dataset is associated to a CCTV or group of CCTVs monitoring a location. All the asscociated CCTVs sends the images only to the corresponding dataset.
    2. Images => Images belong to the datasets, and they stores the path to the image file in the filesystem in the cloud. A image may have muliple annotations. 
    3. Annotations => Annotations belong to the images, and they stores the information of object in the images with bounding box locations. Annotations can be classified into different categories. 
    4. Catgories => List of categories. Each annotation must have one and only category.

Example API to serve this,

Endpoint: /api/dataset/

    Method: GET
    Response: {'datasets': [
        {
            'dataset_id': int, 
            'images': int,
            'annotations': int,
            'name': string,
            'country': string,
            'province': string,
            'city': string,
            'latitude': string,
            'longitude': string
        }, ...
    ]}

    Method: POST
    Params: 
        name: string
        country: string
        province: string
        city: string
        latitude: string
        longitude: string
    Response:
        {'id': int}

Endpoint: /api/dataset/dataset_id

    Method: GET
    Response: {
        'dataset_id': int, 
        'images': int,
        'annotations': int,
        'name': string,
        'country': string,
        'province': string,
        'city': string,
        'latitude': string,
        'longitude': string
    }

    Method: POST
    Params:
        any_key: any_value
    Response: {..}

Endpoint: /api/category

    Method: POST
    Params:
        name: string
    Response: {'category_id': int}

Endpoint: /api/category/category_id

    Method: GET
    Response: {
        category_id: int,
        name: string,
    }

Endpoint: /api/image/

    Method: POST
    file: Image
    Params:
        dataset_id: int
        name: string
        date_captured: datatime
    Response: {'image_id': int}

Endpoint: /api/image/image_id

    Method: GET
    Response: file

Endpoint: /api/annotation

    Method: POST
    Params:
        image_id: int
        category_id: int
        isbbox: Bool
        bbox: [x,y,w,h]
        sementation: [[x1,y1,x2,y2,......,xn,yn]]
        area: int
    Response: {'annotation_id': int}

Endpoint: /api/annotation/annotation_id

    Method: GET
    REsponse: {
        image_id: int,
        category_id: int,
        isbbox: Bool,
        bbox: [x,y,w,h],
        sementation: [[x1,y1,x2,y2,......,xn,yn]],
        area: int
    }

