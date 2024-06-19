from flask import request
from flask_restplus import Namespace, Resource, reqparse, inputs
from flask_login import login_required, current_user
from werkzeug.datastructures import FileStorage
from mongoengine.errors import NotUniqueError
from mongoengine.queryset.visitor import Q
from threading import Thread
from flask import send_file

from google_images_download import google_images_download as gid

from ..util.pagination_util import Pagination
from ..util import query_util, coco_util, profile

from database import (
    ImageModel,
    DatasetModel,
    CategoryModel,
    AnnotationModel,
    ExportModel
)

from PIL import Image
import datetime
import json
import os
import io

from ..cache import cache

import logging
logger = logging.getLogger('gunicorn.error')

api = Namespace('dataset', description='Dataset related operations')

dataset_filter = reqparse.RequestParser()
dataset_filter.add_argument('country', type=str)
dataset_filter.add_argument('province', type=str)
dataset_filter.add_argument('city', type=str)

dataset_create = reqparse.RequestParser()
dataset_create.add_argument('name', required=True)
dataset_create.add_argument('country', type=str)
dataset_create.add_argument('province', type=str)
dataset_create.add_argument('city', type=str)
dataset_create.add_argument('latitude', type=float)
dataset_create.add_argument('longitude', type=float)
dataset_create.add_argument('purpose', type=str)
dataset_create.add_argument('categories', type=list, required=False, location='json',
                            help="List of default categories for sub images")

page_data = reqparse.RequestParser()
page_data.add_argument('page', default=1, type=int)
page_data.add_argument('limit', default=20, type=int)
page_data.add_argument('folder', default='', help='Folder for data')
page_data.add_argument('order', default='file_name', help='Order to display images')
#page_from_to_data = reqparse.RequestParser()
page_data.add_argument('start_date', type=str, default='')
page_data.add_argument('end_date', type=str, default='')

delete_data = reqparse.RequestParser()
delete_data.add_argument('fully', default=False, type=bool,
                         help="Fully delete dataset (no undo)")

coco_upload = reqparse.RequestParser()
coco_upload.add_argument('coco', location='files', type=FileStorage, required=True, help='Json coco')

export = reqparse.RequestParser()
export.add_argument('categories', type=str, default=None, required=False, help='Ids of categories to export')

update_dataset = reqparse.RequestParser()
update_dataset.add_argument('display_name', type=str, help="Name to display on dashboard")
update_dataset.add_argument('categories', location='json', type=list, help="New list of categories")
update_dataset.add_argument('country', type=str, help="country of cctv")
update_dataset.add_argument('province', type=str, help="province of cctv")
update_dataset.add_argument('city', type=str, help="city of cctv")
update_dataset.add_argument('latitude', type=float, help="GPS latitude of the cctv location")
update_dataset.add_argument('longitude', type=float, help="GPS longitude of the cctv location")
update_dataset.add_argument('images_prefix', type=str)
update_dataset.add_argument('start_date', type=str)
update_dataset.add_argument('end_date', type=str)
update_dataset.add_argument('purpose', type=str)
update_dataset.add_argument('youtube_links', type=list)
update_dataset.add_argument('default_annotation_metadata', location='json', type=dict,
                            help="Default annotation metadata")

dataset_youtube = reqparse.RequestParser()
dataset_youtube.add_argument('youtube_links', location='json', type=list, default=[])

dataset_generate = reqparse.RequestParser()
dataset_generate.add_argument('keywords', location='json', type=list, default=[],
                              help="Keywords associated with images")
dataset_generate.add_argument('limit', location='json', type=int, default=100, help="Number of images per keyword")

share = reqparse.RequestParser()
share.add_argument('users', location='json', type=list, default=[], help="List of users")

cs_data = reqparse.RequestParser()
cs_data.add_argument('rejected', location='json', type=list, default=[], help="List of images to filter")
cs_data.add_argument('dummy', location='json', type=bool, default=False)

dataset_refresh = reqparse.RequestParser()
dataset_refresh.add_argument('start_date', type=int)
dataset_refresh.add_argument('end_date', type=int)

pie_limits = reqparse.RequestParser()
pie_limits.add_argument('start_date', default='', type=str)
pie_limits.add_argument('end_date', default='99991231', type=str)
pie_limits.add_argument('frequency', default='', type=str)
#dataset_country = reqparse.RequestParser()
#dataset_country.add_argument('country', required=True)

cctv_config = reqparse.RequestParser()
cctv_config.add_argument('weights_name', default=None, type=str)
cctv_config.add_argument('weights_url', default=None, type=str)
cctv_config.add_argument('frame_height', default=None, type=int)
cctv_config.add_argument('frame_width', default=None, type=int)
cctv_config.add_argument('slice_height', default=None, type=int)
cctv_config.add_argument('slice_width', default=None, type=int)
cctv_config.add_argument('interval', default=20, type=int)
cctv_config.add_argument('key', default=None, type=str)

@api.route('/')
class Dataset(Resource):
    #@login_required
    @api.expect(dataset_filter)
    def get(self):
        """ Returns all datasets or filtered by args"""
        args = dataset_filter.parse_args()
        country = args['country']
        province = args['province']
        city = args['city']
        if country:
            if province:
                if city:
                    return query_util.fix_ids(current_user.datasets.filter(deleted=False, country=country, province=province, city=city).only('id', 'display_name', 'country', 'province', 'city', 'latitude', 'longitude', 'start_date', 'purpose').all())
                return query_util.fix_ids(current_user.datasets.filter(deleted=False, country=country, province=province).all())
            return query_util.fix_ids(current_user.datasets.filter(deleted=False, country=country).all())
        return query_util.fix_ids(current_user.datasets.filter(deleted=False).all())
    
    @api.expect(dataset_create)
    @login_required
    def post(self):
        """ Creates a dataset """
        if current_user.is_admin:
            args = dataset_create.parse_args()
            name = args['name']
            country = args['country']
            province = args['province']
            city = args['city']
            latitude = args['latitude']
            longitude = args['longitude']
            categories = args.get('categories', [])

            category_ids = CategoryModel.bulk_create(categories)

            try:
                dataset = DatasetModel(name=name, display_name=name, categories=category_ids, country=country, province=province, city=city, latitude=latitude, longitude=longitude)
                dataset.save()
            except NotUniqueError:
                return {'message': 'Dataset already exists. Check the undo tab to fully delete the dataset.'}, 400

            return query_util.fix_ids(dataset)
        else: 
            return {'message': 'Only admin users are allowed to create datasets.'}, 403


def download_images(output_dir, args):
    for keyword in args['keywords']:
        response = gid.googleimagesdownload()
        response.download({
            "keywords": keyword,
            "limit": args['limit'],
            "output_directory": output_dir,
            "no_numbering": True,
            "format": "jpg",
            "type": "photo",
            "print_urls": False,
            "print_paths": False,
            "print_size": False
        })

@api.route('/countries')
class DatasetCountires(Resource):
    def get(self):
        datasets = current_user.datasets.only('country')
        countries = set()
        for dataset in datasets:
            if dataset.country is not None:
                countries.add(dataset.country)
        return {"countries": list(countries)}, 200

@api.route('/<country>/provinces')
class DatasetProvinces(Resource):
    #@api.expect(dataset_country)
    def get(self, country):
        #args = dataset_country.parse_args()
        #country = args['country']
        datasets = current_user.datasets.filter(country=country)
        provinces = set()
        for dataset in datasets:
            if dataset.province is not None:
                provinces.add(dataset.province)
        return {"provinces": list(provinces)}, 200

@api.route('/<country>/<province>/cities')
class DatasetCities(Resource):
    def get(self, country, province):
        datasets = current_user.datasets.filter(country=country, province=province)
        cities = set()
        for dataset in datasets:
            if dataset.city is not None:
                cities.add(dataset.city)
        return {"cities": list(cities)}, 200

@api.route('/<country>/<province>/<city>')
class DatasetFiltered(Resource):
    def get(self, country, province, city):
        return query_util.fix_ids(current_user.datasets.filter(country=country, province=province, city=city, deleted=False).all()), 200

@api.route('/<int:dataset_id>/generate')
class DatasetGenerate(Resource):
    @api.expect(dataset_generate)
    @login_required
    def post(self, dataset_id):
        """ Adds images found on google to the dataset """
        args = dataset_generate.parse_args()

        dataset = current_user.datasets.filter(id=dataset_id, deleted=False).first()
        if dataset is None:
            return {"message": "Invalid dataset id"}, 400

        if not dataset.is_owner(current_user):
            return {"message": "You do not have permission to download the dataset's annotations"}, 403

        thread = Thread(target=download_images, args=(dataset.directory, args))
        thread.start()

        return {"success": True}

@api.route('/<int:dataset_id>/config')
class DatasetConfig(Resource):

    def get(self, dataset_id):
        """return configuration settings for cctv camera"""
        dataset = current_user.datasets.filter(id=dataset_id, deleted=False).exclude('key').first()
        return query_util.fix_ids(dataset), 200

    @login_required
    @api.expect(cctv_config)
    def post(self, dataset_id):
        """updates cctv camera configuration"""
        args = cctv_config.parse_args()
        weights = args['weights_name']
        weights_url = args['weights_url']
        frame_width = args['frame_width']
        frame_height = args['frame_height']
        slice_width = args['slice_width']
        slice_height = args['slice_height']
        interval = args['interval']
        key = args['key']

        dataset = current_user.datasets.filter(id=dataset_id, deleted=False).first()

        if weights:
            dataset.update(set__weights=weights)
        if weights_url:
             dataset.update(set__weights_url=weights_url)
        if frame_width:
             dataset.update(set__frame_width=frame_width)
        if frame_height:
             dataset.update(set__frame_height=frame_height)
        if slice_width:
             dataset.update(set__slice_width=slice_width)
        if slice_height:
             dataset.update(set__slice_height=slice_height)
        if interval:
             dataset.update(set__interval=interval)
        if key:
             dataset.update(set__key=key)

        #dataset = current_user.datasets.filter(id=dataset_id, deleted=False).first()
        #return querty_util.fix_ids{dataset}, 200
        return {}, 200

@api.route('/<int:dataset_id>/users')
class DatasetMembers(Resource):

    @login_required
    def get(self, dataset_id):
        """ All users in the dataset """
        args = dataset_generate.parse_args()

        dataset = current_user.datasets.filter(id=dataset_id, deleted=False).first()
        if dataset is None:
            return {"message": "Invalid dataset id"}, 400

        users = dataset.get_users()
        return query_util.fix_ids(users)


@api.route('/<int:dataset_id>/reset/metadata')
class DatasetCleanMeta(Resource):

    @login_required
    def get(self, dataset_id):
        """ All users in the dataset """
        args = dataset_generate.parse_args()

        dataset = current_user.datasets.filter(id=dataset_id, deleted=False).first()
        if dataset is None:
            return {"message": "Invalid dataset id"}, 400

        AnnotationModel.objects(dataset_id=dataset.id)\
            .update(metadata=dataset.default_annotation_metadata)
        ImageModel.objects(dataset_id=dataset.id)\
            .update(metadata={})

        return {'success': True}

@api.route('/<int:dataset_id>/pie_stats')
class DatasetPiestats(Resource):

    @api.expect(pie_limits)
    @cache.cached(timeout=120, query_string=True)
    def get(self, dataset_id):
        args = pie_limits.parse_args()
        start_date = args['start_date']
        end_date = args['end_date']

        # Validate the dataset
        dataset = current_user.datasets.filter(id=dataset_id, deleted=False).first()
        if dataset is None:
            return {"message": "Invalid dataset id"}, 400

        category_count = {}

        if start_date:
            # Ensure that the indexes are used by filtering on the date range and dataset_id
            images = ImageModel.objects(
                dataset_id=dataset.id, 
                deleted=False, 
                file_name__gte=start_date, 
                file_name__lte=end_date
            ).only('id').timeout(False)

            image_ids = [image.id for image in images]
            
            if not image_ids:
                return category_count, 200  # Return empty if no images found within date range

            # Filter annotations based on the image IDs
            pipeline = [
                {'$match': {
                    'dataset_id': dataset.id, 
                    'deleted': False, 
                    'image_id': {'$in': image_ids}
                }},
                {'$group': {
                    '_id': '$category_id',
                    'count': {'$sum': 1}
                }}
            ]
            result = list(AnnotationModel.objects.aggregate(*pipeline))
        else:
            # Aggregate annotations directly by category_id without date filter
            pipeline = [
                {'$match': {'dataset_id': dataset.id, 'deleted': False}},
                {'$group': {
                    '_id': '$category_id',
                    'count': {'$sum': 1}
                }}
            ]
            result = list(AnnotationModel.objects.aggregate(*pipeline))

        # Prepare the category count dictionary
        if result:
            category_ids = [entry['_id'] for entry in result]
            categories = CategoryModel.objects(id__in=category_ids)
            category_dict = {str(cat.id): cat.name for cat in categories}

            for entry in result:
                category_name = category_dict.get(str(entry['_id']))
                if category_name:
                    category_count[category_name] = entry['count']

        return category_count, 200

    # def get(self, dataset_id):
    #     args = pie_limits.parse_args()
    #     start_date = args['start_date']
    #     end_date = args['end_date']

    #     dataset = current_user.datasets.filter(id=dataset_id, deleted=False).first()
    #     if dataset is None:
    #         return {"message": "Invalid dataset id"}, 400
    #     if not start_date:
    #         annotations = AnnotationModel.objects(dataset_id=dataset.id, deleted=False)

    #         category_count = dict()
    #         for category in dataset.categories:
    #             cat_name = CategoryModel.objects(id=category).first().name
    #             cat_count = annotations.filter(category_id=category).count()
    #             category_count[cat_name] = cat_count
    #     else:
    #         images = ImageModel.objects(dataset_id=dataset.id, deleted=False, file_name__gte=start_date, file_name__lte=end_date)
    #         image_ids = [image.id for image in images]

    #         # Filter annotations based on the dataset, deletion status, and associated image IDs
    #         annotations = AnnotationModel.objects(dataset_id=dataset.id, deleted=False, image_id__in=image_ids)
    #         category_count = dict()
    #         for category in dataset.categories:
    #             cat_name = CategoryModel.objects(id=category).first().name  # Access directly without dictionary access
    #             cat_count = annotations.filter(category_id=category).count()
    #             category_count.update({str(cat_name): cat_count})
    #     return category_count, 200

    # def get(self, dataset_id):
    #     args = pie_limits.parse_args()
    #     start_date = args['start_date']
    #     end_date = args['end_date']

    #     dataset = current_user.datasets.filter(id=dataset_id, deleted=False).first()
    #     if dataset is None:
    #         return {"message": "Invalid dataset id"}, 400
    #     if start_date:
    #         images = ImageModel.objects(dataset_id=dataset.id, deleted=False, file_name__gte=start_date, file_name__lte=end_date)
    #         image_ids = [image.id for image in images]

    #         # Filter annotations based on the dataset, deletion status, and associated image IDs
    #         annotations = AnnotationModel.objects(dataset_id=dataset.id, deleted=False, image_id__in=image_ids)
    #         category_count = dict()
    #         for category in dataset.categories:
    #             cat_name = CategoryModel.objects(id=category).first().name  # Access directly without dictionary access
    #             cat_count = annotations.filter(category_id=category).count()
    #             category_count.update({str(cat_name): cat_count}) 
    #     else:
    #         match_conditions = {'dataset_id': dataset.id, 'deleted': False}
    #         pipeline = [
    #             {'$match': match_conditions},
    #             {'$group': {
    #                 '_id': '$category_id',
    #                 'count': {'$sum': 1}
    #             }}
    #         ]

    #         result = AnnotationModel.objects.aggregate(*pipeline)

    #         category_count = {}
    #         for entry in result:
    #             category = CategoryModel.objects(id=entry['_id']).first()
    #             if category:
    #                 category_count[category.name] = entry['count']

    #     return category_count, 200

@api.route('/<int:dataset_id>/line_stats')
class DatasetLinestats(Resource):

    @api.expect(pie_limits)
    @cache.cached(timeout=60, query_string=True)
    def get(self, dataset_id):

        args = pie_limits.parse_args()
        start_date = args['start_date']
        end_date = args['end_date']

        dataset = current_user.datasets.filter(id=dataset_id, deleted=False).first()
        if dataset is None:
            return {"message": "Invalid dataset id"}, 400

        si = 0
        if dataset.images_prefix:
            start_date = dataset.images_prefix + start_date
            end_date = dataset.images_prefix + end_date
            si = len(dataset.images_prefix)

        res = ImageModel.objects(dataset_id=dataset.id, deleted=False, file_name__gte=start_date, file_name__lte=end_date, num_annotations__gt=0).aggregate(
            {
                "$project": {
                    "day": {
                        "$substr": ["$file_name", si, si+8]
                    },
                    "category_ids": 1
                }
            },
            {
                "$unwind": {
                    "path": "$category_ids"
                }
            },
            {
                "$group": {
                    "_id": {
                        "day": "$day",
                        "category_id": "$category_ids"
                    }, 
                    "count": {
                        "$sum": 1
                    }
                }
            },
            {
                "$group": {
                    "_id": "$_id.day",
                    "stats": {
                        "$push": {
                            "category_id": "$_id.category_id",
                            "count": "$count"
                        }
                    }
                }
            },
            {
                "$sort": {"_id": 1}
            },
            {
                "$project": {
                    "_id": 0,
                    "date": "$_id",
                    "stats": 1
                }
            }
        )

        line_data = {'data': list(res)}

        logger.info(f'days, {res}')

        return line_data, 200

@api.route('/<int:dataset_id>/new_line_stats')
class DatasetNLinestats(Resource):

    @api.expect(pie_limits)
    @cache.cached(timeout=60, query_string=True)
    def get(self, dataset_id):

        args = pie_limits.parse_args()
        start_date = args['start_date']
        end_date = args['end_date']

        dataset = current_user.datasets.filter(id=dataset_id, deleted=False).first()
        if dataset is None:
            return {"message": "Invalid dataset id"}, 400


        res = ImageModel.objects(dataset_id=dataset.id, deleted=False, file_name__gte=start_date, file_name__lte=end_date, num_annotations__gt=0).aggregate(
            {
                "$project": {
                    "day": {
                        "$substr": ["$file_name", 0, 8]
                    },
                    "instances": {
                        "$objectToArray": "$instances"
                    }
                }
            },
            {
                "$unwind": {
                    "path": "$instances"
                }
            },
            {
                "$group": {
                    "_id": {
                        "day": "$day",
                        "category_id": "$instances.k"
                    }, 
                    "count": {
                        "$sum": "$instances.v"
                    }
                }
            },
            {
                "$group": {
                    "_id": "$_id.day",
                    "stats": {
                        "$push": {
                            "category_id": "$_id.category_id",
                            "count": "$count"
                        }
                    }
                }
            },
            {
                "$sort": {"_id": 1}
            },
            {
                "$project": {
                    "_id": 0,
                    "date": "$_id",
                    "stats": 1
                }
            }
        )

        line_data = {'data': list(res)}

        logger.info(f'days, {res}')

        return line_data, 200

@api.route('/<int:dataset_id>/highlights')
class DatasetHighlights(Resource):

    def get(self, dataset_id):

        dataset = current_user.datasets.filter(id=dataset_id, deleted=False).first()
        if dataset is None:
            return {"message": "Invalid dataset id"}, 400
        directory = dataset.directory+'.highlights'
        #logger.info(f'highlights at, {directory}')
        if not os.path.isdir(directory):
            return {"highlights": []}, 400

        highlights = [f for f in sorted(os.listdir(directory)) if not f.startswith('.')]
        # to-do, send imahes from .highlight folder

        return {"highlights": highlights}, 200

@api.route('/<int:dataset_id>/highlights/<file_name>')
class DatasetHighlightsImage(Resource):

    def get(self, dataset_id, file_name):
        """ sends the highlight image"""
        dataset = current_user.datasets.filter(id=dataset_id, deleted=False).first()
        if dataset is None:
            return {"message": "Invalid dataset id"}, 400
        directory = dataset.directory+'.highlights'
        if not os.path.isdir(directory):
            return {"message": "No highlights"}, 400
        file_path = os.path.join(directory, file_name)
        if not os.path.isfile(file_path):
            return {"message": "Invalid highlight"}, 400
        pil_image = Image.open(file_path)
        image_io = io.BytesIO()
        pil_image = pil_image.convert("RGB")
        pil_image.save(image_io, "JPEG", quality=90)
        image_io.seek(0)
        return send_file(image_io, attachment_filename=file_name, as_attachment=False)

@api.route('/<int:dataset_id>/stats')
class DatasetStats(Resource):

    # @login_required
    @cache.cached(timeout=60, query_string=True)
    def get(self, dataset_id):
        """ All users in the dataset """
        args = dataset_generate.parse_args()

        dataset = current_user.datasets.filter(id=dataset_id, deleted=False).first()
        if dataset is None:
            return {"message": "Invalid dataset id"}, 400

        images = ImageModel.objects(dataset_id=dataset.id, deleted=False)
        #num_images_cs_not_annotated = len(ImageModel.objects(dataset_id=dataset.id, cs_annotated=[], deleted=False))
        annotated_images = images.filter(annotated=True)
        annotations = AnnotationModel.objects(dataset_id=dataset_id, deleted=False)

        # Calculate annotation counts by category in this dataset
        category_count = dict()
        image_category_count = dict()
        for category in dataset.categories:

            # Calculate the annotation count in the current category in this dataset
            cat_name = CategoryModel.objects(id=category).first()['name']
            #cat_count = AnnotationModel.objects(dataset_id=dataset_id, category_id=category, deleted=False).count()
            cat_count = annotations.filter(category_id=category).count()
            category_count.update({str(cat_name): cat_count})

            # Calculate the annotated images count in the current category in this dataset
            #image_count = len(AnnotationModel.objects(dataset_id=dataset_id, category_id=category, deleted=False).distinct('image_id'))
            image_count = len(annotations.filter(category_id=category).distinct('image_id'))
            image_category_count.update({str(cat_name): image_count})

        stats = {
            'total': {
                'Users': dataset.get_users().count(),
                'Images': images.count(),
                'Annotated Images': annotated_images.count(),
                #'CS Annotated Images': num_images_cs_not_annotated,
                'Annotations': annotations.count(),
                'Categories': len(dataset.categories),
                'Time Annotating (s)': (images.sum('milliseconds') or 0) / 1000
            },
            'average': {
                'Image Size (px)': images.average('width'),
                'Image Height (px)': images.average('height'),
                'Annotation Area (px)': annotations.average('area'),
                'Time (ms) per Image': images.average('milliseconds') or 0,
                'Time (ms) per Annotation': annotations.average('milliseconds') or 0
            },
            'categories': category_count,
            'images_per_category': image_category_count
        }
        return stats

@api.route('/<int:dataset_id>/cs_stats')
class DatasetcsStats(Resource):

    # @login_required
    def get(self, dataset_id):
        """ All users in the dataset """

        dataset = current_user.datasets.filter(id=dataset_id, deleted=False).first()
        if dataset is None:
            return {"message": "Invalid dataset id"}, 400

        images = ImageModel.objects(dataset_id=dataset.id, deleted=False)
        num_images_cs_not_annotated = len(ImageModel.objects(dataset_id=dataset.id, cs_annotated=[], deleted=False))

        cs_stats = {
            'total': {
                'Images': images.count(),
                'CS Annotated Images': num_images_cs_not_annotated,
            }
        }
        return cs_stats

@api.route('/<int:dataset_id>/cats')
class DatasetCats(Resource):

    # @login_required
    @cache.cached(timeout=60, query_string=True)
    def get(self, dataset_id):
        """ All users in the dataset """

        dataset = current_user.datasets.filter(id=dataset_id, deleted=False).first()
        if dataset is None:
            return {"message": "Invalid dataset id"}, 400

        category_dict = dict()
        for category in dataset.categories:

            cat_name = CategoryModel.objects(id=category).first()['name']
            category_dict.update({str(cat_name): category})

        res = {
            'categories': category_dict,
        }
        return res

@api.route('/<int:dataset_id>')
class DatasetId(Resource):

    @login_required
    def delete(self, dataset_id):
        """ Deletes dataset by ID (only owners)"""

        dataset = DatasetModel.objects(id=dataset_id, deleted=False).first()

        if dataset is None:
            return {"message": "Invalid dataset id"}, 400

        if not current_user.can_delete(dataset):
            return {"message": "You do not have permission to delete the dataset"}, 403

        dataset.update(set__deleted=True, set__deleted_date=datetime.datetime.now())
        return {"success": True}

    @login_required
    @api.expect(update_dataset)
    def post(self, dataset_id):

        """ Updates dataset by ID """

        dataset = current_user.datasets.filter(id=dataset_id, deleted=False).first()
        if dataset is None:
            return {"message": "Invalid dataset id"}, 400

        args = update_dataset.parse_args()
        display_name = args.get('display_name')
        categories = args.get('categories')
        country = args.get('country')
        province = args.get('province')
        city = args.get('city')
        latitude = args.get('latitude')
        longitude = args.get('longitude')
        start_date = args.get('start_date')
        end_date = args.get('end_date')
        images_prefix = args.get('images_prefix')
        default_annotation_metadata = args.get('default_annotation_metadata')
        set_default_annotation_metadata = args.get('set_default_annotation_metadata')
        camera_purpose = args.get('purpose')
        youtube_links = args.get('youtube_links', [])

        if youtube_links != []:
            dataset.update(add_to_set__youtube_links=youtube_links)

        if camera_purpose is not None:
            dataset.update(set__purpose=camera_purpose)

        if display_name is not None:
            dataset.update(set__display_name=display_name)
        if country is not None:
            dataset.update(set__country=country)
        if province is not None:
            dataset.update(set__province=province)
        if city is not None:
            dataset.update(set__city=city)
        if latitude is not None:
            dataset.update(set__latitude=latitude)
        if longitude is not None:
            dataset.update(set__longitude=longitude)
        if start_date is not None:
            dataset.update(set__start_date=start_date)
        if categories is not None:
            dataset.categories = CategoryModel.bulk_create(categories)
        if  images_prefix is not None:
            dataset.update(set__images_prefix=images_prefix)

        if default_annotation_metadata is not None:

            update = {}
            for key, value in default_annotation_metadata.items():
                if key not in dataset.default_annotation_metadata:
                    update[f'set__metadata__{key}'] = value

            dataset.default_annotation_metadata = default_annotation_metadata

            if len(update.keys()) > 0:
                AnnotationModel.objects(dataset_id=dataset.id, deleted=False)\
                    .update(**update)

        dataset.update(
            categories=dataset.categories,
            default_annotation_metadata=dataset.default_annotation_metadata
        )

        return {"success": True}

@api.route('/<int:dataset_id>/youtube')
class DatasetIdYoutube(Resource):

    def get(self, dataset_id):
        dataset = current_user.datasets.filter(id=dataset_id, deleted=False).first()
        if dataset is None:
            return {"message": "Invalid dataset id"}, 400
        return {"dataset_id": dataset_id, "youtube_links": dataset.youtube_links}, 200

    @api.expect(dataset_youtube)
    @login_required
    def post(self, dataset_id):
        dataset = current_user.datasets.filter(id=dataset_id, deleted=False).first()
        if dataset is None:
            return {"message": "Invalid dataset id"}, 400
        args = dataset_youtube.parse_args()
        youtube_links = args.get('youtube_links', [])
        if youtube_links != []:
            logger.info(f'youtube_links: {youtube_links}')
            dataset.update(pull_all__youtube_links=youtube_links)
        return {"success": True}

    @api.expect(dataset_youtube)
    @login_required
    def delete(self, dataset_id):
        dataset = current_user.datasets.filter(id=dataset_id, deleted=False).first()
        if dataset is None:
            return {"message": "Invalid dataset id"}, 400
        args = dataset_youtube.parse_args()
        youtube_links = args.get('youtube_links', [])
        if youtube_links != []:
            dataset.update(pull_all__youtube_links=youtube_links)
        return {"success": True}

@api.route('/<int:dataset_id>/share')
class DatasetIdShare(Resource):
    @api.expect(share)
    @login_required
    def post(self, dataset_id):
        args = share.parse_args()

        dataset = current_user.datasets.filter(id=dataset_id, deleted=False).first()
        if dataset is None:
            return {"message": "Invalid dataset id"}, 400

        if not dataset.is_owner(current_user):
            return {"message": "You do not have permission to share this dataset"}, 403

        dataset.update(users=args.get('users'))

        return {"success": True}


@api.route('/data')
class DatasetData(Resource):
    @api.expect(page_data)
    #@login_required
    #@cache.cached(timeout=10, query_string=True)
    def get(self):
        """ Endpoint called by dataset viewer client """

        args = page_data.parse_args()
        limit = args['limit']
        page = args['page']
        folder = args['folder']

        datasets = current_user.datasets.filter(deleted=False)
        pagination = Pagination(datasets.count(), limit, page)
        datasets = datasets[pagination.start:pagination.end]

        datasets_json = []
        for dataset in datasets:
            dataset_json = query_util.fix_ids(dataset)
            images = ImageModel.objects(dataset_id=dataset.id, deleted=False)

            dataset_json['numberImages'] = images.count()
            dataset_json['numberAnnotated'] = images.filter(annotated=True).count()
            dataset_json['permissions'] = dataset.permissions(current_user)

            first = images.first()
            if first is not None:
                dataset_json['first_image_id'] = images.first().id
            datasets_json.append(dataset_json)

        return {
            "pagination": pagination.export(),
            "folder": folder,
            "datasets": datasets_json,
            "categories": query_util.fix_ids(current_user.categories.filter(deleted=False).all())
        }

@api.route('/<int:dataset_id>/data')
class DatasetDataId(Resource):

    @profile
    @api.expect(page_data)
    # @login_required
    # ************Add condition if dataset is_publc?
    @cache.cached(timeout=60, query_string=True)
    def get(self, dataset_id):
        """ Endpoint called by image viewer client """

        parsed_args = page_data.parse_args()
        per_page = parsed_args.get('limit')
        page = parsed_args.get('page') - 1
        folder = parsed_args.get('folder')
        order = parsed_args.get('order')

        start_date = parsed_args.get('start_date')
        end_date = parsed_args.get('end_date')

        args = dict(request.args)

        # Check if dataset exists
        dataset = current_user.datasets.filter(id=dataset_id, deleted=False).first()
        if dataset is None:
            return {'message', 'Invalid dataset id'}, 400

        dataset_start_date = str(dataset.start_date)

        numeric_filter = filter(str.isdigit, dataset_start_date)
        dataset_start_date = "".join(numeric_filter)

        logger.info(f'date, {dataset_start_date}')
        if dataset.end_date:
            dataset_end_date = str(dataset.end_date)
        else:
            last_image = current_user.images.filter(dataset_id=dataset_id, deleted=False).only('file_name').order_by('-file_name').first()
            if last_image:
                dataset_end_date = last_image.file_name.split('_')[-1].split('-')[0]
            else:
                dataset_end_date = dataset_start_date

        numeric_filter = filter(str.isdigit, dataset_end_date)
        dataset_end_date = "".join(numeric_filter)

        # Make sure folder starts with is in proper format
        if len(folder) > 0:
            folder = folder[0].strip('/') + folder[1:]
            if folder[-1] != '/':
                folder = folder + '/'

        # Get directory
        directory = os.path.join(dataset.directory, folder)
        if not os.path.exists(directory):
            return {'message': 'Directory does not exist.'}, 400

        # Remove parsed arguments
        for key in parsed_args:
            args.pop(key, None)

        # Generate query from remaining arugments
        query = {}
        for key, value in args.items():
            lower = value.lower()
            if lower in ["true", "false"]:
                value = json.loads(lower)

            if len(lower) != 0:
                query[key] = value

        # Change category_ids__in to list
        if 'category_ids__in' in query.keys():
            query['category_ids__in'] = [int(x) for x in query['category_ids__in'].split(',')]

        # Initialize mongo query with required elements:
        query_build = Q(dataset_id=dataset_id)
        query_build &= Q(path__startswith=directory)
        query_build &= Q(deleted=False)

        # Define query names that should use complex logic:
        complex_query = ['annotated', 'category_ids__in']

        # Add additional 'and' arguments to mongo query that do not require complex_query logic
        for key in query.keys():
            if key not in complex_query:
                query_dict = {}
                query_dict[key] = query[key]
                query_build &= Q(**query_dict)

        # Add additional arguments to mongo query that require more complex logic to construct
        if 'annotated' in query.keys():

            if 'category_ids__in' in query.keys() and query['annotated']:

                # Only show annotated images with selected category_ids
                query_dict = {}
                query_dict['category_ids__in'] = query['category_ids__in']
                query_build &= Q(**query_dict)

            else:

                # Only show non-annotated images
                query_dict = {}
                query_dict['annotated'] = query['annotated']
                query_build &= Q(**query_dict)

        elif 'category_ids__in' in query.keys():

            # Ahow annotated images with selected category_ids or non-annotated images
            query_dict_1 = {}
            query_dict_1['category_ids__in'] = query['category_ids__in']

            query_dict_2 = {}
            query_dict_2['annotated'] = False
            query_build &= (Q(**query_dict_1) | Q(**query_dict_2))

        if start_date != '' or end_date != '':
            if dataset.images_prefix is not None:
                logger.info(f'using prefix {dataset.images_prefix}')
                start_date = dataset.images_prefix+start_date
                end_date = dataset.images_prefix+end_date
            query_dict3 = {}
            if start_date != '':
                query_dict3['file_name__gte'] = start_date
            if end_date != '':
                query_dict3['file_name__lte'] = end_date
            query_build &= Q(**query_dict3)

        # Perform mongodb query
        images = current_user.images \
            .filter(query_build) \
            .order_by('-file_name').only('id', 'file_name', 'annotating', 'annotated', 'num_annotations', 'category_ids')

        total = images.count()
        pages = int(total/per_page) + 1

        images = images.skip(page*per_page).limit(per_page)
        images_json = query_util.fix_ids(images)

        # for image in images:
        #     image_json = query_util.fix_ids(image)

        #     query = AnnotationModel.objects(image_id=image.id, deleted=False)
        #     category_ids = query.distinct('category_id')
        #     categories = CategoryModel.objects(id__in=category_ids).only('name', 'color')

        #     image_json['annotations'] = query.count()
        #     image_json['categories'] = query_util.fix_ids(categories)

        #     images_json.append(image_json)


        subdirectories = [f for f in sorted(os.listdir(directory))
                          if os.path.isdir(directory + f) and not f.startswith('.')]

        categories = CategoryModel.objects(id__in=dataset.categories).only('id', 'name')

        return {
            "total": total,
            "start_date": dataset_start_date,
            "end_date": dataset_end_date,
            "per_page": per_page,
            "pages": pages,
            "page": page,
            "images": images_json,
            "folder": folder,
            "directory": directory,
            "dataset": query_util.fix_ids(dataset),
            "categories": query_util.fix_ids(categories),
            "subdirectories": subdirectories
        }




# -----------------------------------------------------------working below -------------------------------------------------------------


# get random image from database
# expects dataset id and return a image for annotation
# filetrs: cs_annotating: false & cs_annotated == [] (empty) 

@api.route('/<int:dataset_id>/random_image')
class DatasetRandomDataId(Resource):

    @profile
    @api.expect(cs_data)
    # @login_required
    # ************Add condition if dataset is_publc?
    def post(self, dataset_id):
        """ Endpoint called by cs client """

        args = cs_data.parse_args()
        # logger.info(f'cs args are, {args}')
        rejected_list = args.get('rejected')

        # Check if dataset exists
        dataset = current_user.datasets.filter(id=dataset_id, deleted=False).first()
        if dataset is None:
            return {'message', 'Invalid dataset id'}, 400
                
        # Make sure folder starts with is in proper format

        # to do
        # until get request args use ''
        folder = ''

        if len(folder) > 0:
            folder = folder[0].strip('/') + folder[1:]
            if folder[-1] != '/':
                folder = folder + '/'

        # Get directory
        directory = os.path.join(dataset.directory, folder)
        if not os.path.exists(directory):
            return {'message': 'Directory does not exist.'}, 400

        # Initialize mongo query with required elements:
        query_build = Q(dataset_id=dataset_id)
        query_build &= Q(path__startswith=directory)
        query_build &= Q(deleted=False)
        query_build &= Q(cs_annotating=False)
        query_build &= Q(cs_annotated=[])
        query_build &= Q(id__nin=rejected_list)

        # logger.info(f'rejected list is {rejected_list}')
        
        # Perform mongodb query
        image = current_user.images \
            .filter(query_build) \
            .only('id', 'file_name', 'annotating', 'annotated', 'num_annotations', 'path').first()

        if len(rejected_list):
            if rejected_list[-1]:
                unlock_image = current_user.images.filter(id=rejected_list[-1], cs_annotated=[]).first()
                if unlock_image:
                    logger.info(f'unlocking rejected image, {rejected_list[-1]}')
                    unlock_image.update(cs_annotating=False)
        
        # set loaded to cs_annotating to lock it
        if image is not None:
            # to do
            # use this update until using sockets ()
            # 
            image.update(set__cs_annotating=True)
            image_id = image.id
            image = current_user.images.filter(id=image_id, deleted=False).first()
            return {
                "image_id": image.id,
                "image_path": image.path,
                "cs_annotating": image.cs_annotating,
                "rejected_list": rejected_list
            }
        else:
            image = current_user.images.filter(cs_annotated=[]).first()    
            return {
                "image_id": image.id,
                "all_images_locked": True
            }

# -----------------------------------------------------------working on above -------------------------------------------------------------


@api.route('/<int:dataset_id>/exports')
class DatasetExports(Resource):

    @login_required
    def get(self, dataset_id):
        """ Returns exports of images and annotations in the dataset (only owners) """
        dataset = current_user.datasets.filter(id=dataset_id).first()

        if dataset is None:
            return {"message": "Invalid dataset ID"}, 400
        
        if not current_user.can_download(dataset):
            return {"message": "You do not have permission to download the dataset's annotations"}, 403
        
        exports = ExportModel.objects(dataset_id=dataset.id).order_by('-created_at').limit(50)

        dict_export = []
        for export in exports:

            time_delta = datetime.datetime.utcnow() - export.created_at
            dict_export.append({
                'id': export.id,
                'ago': query_util.td_format(time_delta),
                'tags': export.tags
            })

        return dict_export


@api.route('/<int:dataset_id>/export')
class DatasetExport(Resource):

    @api.expect(export)
    @login_required
    def get(self, dataset_id):

        args = export.parse_args()
        categories = args.get('categories')
        
        if len(categories) == 0:
            categories = []

        if len(categories) > 0 or isinstance(categories, str):
            categories = [int(c) for c in categories.split(',')]

        dataset = DatasetModel.objects(id=dataset_id).first()
        
        if not dataset:
            return {'message': 'Invalid dataset ID'}, 400
        
        return dataset.export_coco(categories=categories)
    
    @api.expect(coco_upload)
    @login_required
    def post(self, dataset_id):
        """ Adds coco formatted annotations to the dataset """
        args = coco_upload.parse_args()
        coco = args['coco']

        dataset = current_user.datasets.filter(id=dataset_id).first()
        if dataset is None:
            return {'message': 'Invalid dataset ID'}, 400

        return dataset.import_coco(json.load(coco))


@api.route('/<int:dataset_id>/coco')
class DatasetCoco(Resource):

    #@login_required
    def get(self, dataset_id):
        """ Returns coco of images and annotations in the dataset (only owners) """
        dataset = current_user.datasets.filter(id=dataset_id).first()

        if dataset is None:
            return {"message": "Invalid dataset ID"}, 400

        if not current_user.can_download(dataset):
            return {"message": "You do not have permission to download the dataset's annotations"}, 403

        #return coco_util.get_dataset_coco(dataset)

        coco = {
            'images': [],
            'categories': [],
            'annotations': []
        }

        categories = CategoryModel.objects(deleted=False).exclude('deleted_date').in_bulk(dataset.categories).items()

        for category in categories:
            category = query_util.fix_ids(category[1])

            del category['deleted']
            if len(category.get('keypoint_labels', [])) > 0:
                category['keypoints'] = category.pop('keypoint_labels')
                category['skeleton'] = category.pop('keypoint_edges')
            else:
                del category['keypoint_edges']
                del category['keypoint_labels']

            coco.get('categories').append(category)

        dataset = query_util.fix_ids(dataset)

        images = ImageModel.objects(deleted=False, dataset_id=dataset.get('id'), annotated=True).exclude('deleted_date')
        images = query_util.fix_ids(images)
        annotations = AnnotationModel.objects(deleted=False, dataset_id=dataset.get('id')).exclude('deleted_date', 'paper_object')
        annotations = query_util.fix_ids(annotations)

        coco['images'] = images
        coco['annotations'] =  annotations

        return coco, 200

    @api.expect(coco_upload)
    @login_required
    def post(self, dataset_id):
        """ Adds coco formatted annotations to the dataset """
        args = coco_upload.parse_args()
        coco = args['coco']

        dataset = current_user.datasets.filter(id=dataset_id).first()
        if dataset is None:
            return {'message': 'Invalid dataset ID'}, 400

        return dataset.import_coco(json.load(coco))


@api.route('/coco/<int:import_id>')
class DatasetCocoId(Resource):

    @login_required
    def get(self, import_id):
        """ Returns current progress and errors of a coco import """
        coco_import = CocoImportModel.objects(
            id=import_id, creator=current_user.username).first()

        if not coco_import:
            return {'message': 'No such coco import'}, 400

        return {
            "progress": coco_import.progress,
            "errors": coco_import.errors
        }


@api.route('/<int:dataset_id>/scan')
class DatasetScan(Resource):
    
    @login_required
    def get(self, dataset_id):

        dataset = DatasetModel.objects(id=dataset_id).first()
        
        if not dataset:
            return {'message': 'Invalid dataset ID'}, 400
        
        return dataset.scan()

@api.route('/<int:dataset_id>/delete_empty_images')
class DatasetDelEmIm(Resource):
    
    @api.expect(dataset_refresh)
    @login_required
    def get(self, dataset_id):

        args = dataset_refresh.parse_args()
        start_date = args['start_date']
        end_date = args['end_date']

        dataset = DatasetModel.objects(id=dataset_id).first()
        
        if not dataset:
            return {'message': 'Invalid dataset ID'}, 400
        
        if start_date > end_date:
            return {'message': 'Invalid date range'}, 400
        
        return dataset.delete_empty_images(str(start_date), str(end_date))

@api.route('/<int:dataset_id>/cs_refersh')
class DatasetRefresh(Resource):
    
    # @api.expect(dataset_refresh)
    @login_required
    def get(self, dataset_id):

        # args = dataset_refresh.parse_args()
        # dataset_id = args['dataset_id']

        images = ImageModel.objects(dataset_id=dataset_id)
        image_refresh_count = 0
        image_annotated_count = 0
        image_count = images.count()
        image_json = query_util.fix_ids(images)
        for image in images:
            if image.cs_annotated != []:
                image_annotated_count += 1
            else:
                image.update(set__cs_annotating=False, set__cs_annotated=[])
                image_refresh_count += 1
        return {'image_refresh_count': image_refresh_count, 'total_image_count': image_count, 'images': image_json}


@api.route('/<int:dataset_id>/empty_images')
class DatasetEmptyimages(Resource):

    def get(self, dataset_id):
        """returns list of images and ids which are predicted yet"""

        #images = ImageModel.objects(deleted=False, dataset_id=dataset_id, is_predicted_with=False).only('id', 'file_name', 'path').order_by('id').all()
        #images = ImageModel.objects(deleted=False, dataset_id=dataset_id, instances={}).only('id', 'file_name', 'path').order_by('id').all()
        images = ImageModel.objects(deleted=False, dataset_id=dataset_id, instances__exists=True, instances__ne={}).only('id', 'file_name', 'path').order_by('id').all()

        return query_util.fix_ids(images), 200

@api.route('/<int:dataset_id>/refresh')
class DatasetRefresh(Resource):

    @api.expect(dataset_refresh)
    @login_required
    def get(self, dataset_id):

        args = dataset_refresh.parse_args()
        start_date = args['start_date']
        end_date = args['end_date']

        dataset = DatasetModel.objects(id=dataset_id).first()
        
        if not dataset:
            return {'message': 'Invalid dataset ID'}, 400
        
        if start_date > end_date:
            return {'message': 'Invalid date range'}, 400

        dataset.refresh(str(start_date), str(end_date))