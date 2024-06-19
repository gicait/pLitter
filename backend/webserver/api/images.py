from flask_restplus import Namespace, Resource, reqparse
from flask_login import login_required, current_user
from werkzeug.datastructures import FileStorage
from flask import send_file

from ..util import query_util, coco_util, thumbnails
from database import (
    ImageModel,
    DatasetModel,
    AnnotationModel
)

from PIL import Image
import datetime
import os
import io

import logging
logger = logging.getLogger('gunicorn.error')

api = Namespace('image', description='Image related operations')


image_all = reqparse.RequestParser()
image_all.add_argument('fields', required=False, type=str)
image_all.add_argument('page', default=1, type=int)
image_all.add_argument('per_page', default=50, type=int, required=False)

image_upload = reqparse.RequestParser()
image_upload.add_argument('image', location='files',
                          type=FileStorage, required=True,
                          help='PNG or JPG file')
image_upload.add_argument('dataset_id', required=True, type=int,
                          help='Id of dataset to insert image into')
image_upload.add_argument('key', required=False, default=None, type=str, help='secret key for image upload')

image_download = reqparse.RequestParser()
image_download.add_argument('asAttachment', type=bool, default=False)
image_download.add_argument('thumbnail', type=bool, default=False)
image_download.add_argument('width', type=int)
image_download.add_argument('height', type=int)

copy_annotations = reqparse.RequestParser()
copy_annotations.add_argument('category_ids', location='json', type=list,
                              required=False, default=None, help='Categories to copy')

image_updates = reqparse.RequestParser()
image_updates.add_argument('cs_annotating', location='json', type=bool, default=False)
image_updates.add_argument('is_annotations_added', location='json', type=bool, default=False) 

flag_args = reqparse.RequestParser()
flag_args.add_argument('image_id', location='json', type=int)
flag_args.add_argument('is_flagged', location='json', type=bool, default=False)

image_preds = reqparse.RequestParser()
image_preds.add_argument('image_id', required=True)
image_preds.add_argument('predictions', required=True)

@api.route('/')
class Images(Resource):

    @api.expect(image_all)
    @login_required
    def get(self):
        """ Returns all images """
        args = image_all.parse_args()
        per_page = args['per_page']
        page = args['page']-1
        fields = args.get('fields', '')

        images = current_user.images.filter(deleted=False)
        total = images.count()
        pages = int(total/per_page) + 1

        images = images.skip(page*per_page).limit(per_page)
        if fields:
            images = images.only(*fields.split(','))

        return {
            "total": total,
            "pages": pages,
            "page": page,
            "fields": fields,
            "per_page": per_page,
            "images": query_util.fix_ids(images.all())
        }

    @api.expect(image_upload)
    # @login_required
    def post(self):
        """ Creates an image """
        args = image_upload.parse_args()
        image = args['image']
        logger.info(f'Image post with filename: {image.filename}')
        dataset_id = args['dataset_id']
        dataset_key = args['key']

        try:
            dataset = DatasetModel.objects.get(id=dataset_id)
        except:
            return {'message': 'dataset does not exist'}, 400

        # check if current user exists or dataset is public
        # if current_user or dataset['is_public']:

        logger.info(f'Image upload with key {dataset_key}')
        if dataset_key == dataset.key:
            directory = dataset.directory
            if image.filename[0:8].isdigit():
                path = os.path.join(directory, image.filename[0:8], image.filename)
                os.makedirs(os.path.join(directory, image.filename[0:8]), exist_ok=True)    
            else:
                path = os.path.join(directory, image.filename)

            if os.path.exists(path):
                logger.info(f'file already exists {image.filename}')
                db_image = current_user.images.filter(dataset_id=dataset_id, path=path).first()
                if db_image is not None:
                    return {'message': 'file already exists', 'image_id': db_image.id}, 400

            try:
                pil_image = Image.open(io.BytesIO(image.read()))
                pil_image.save(path)
                # db_image = ImageModel.create_from_path(path, dataset_id).save()
                db_image = ImageModel()
                db_image.file_name = os.path.basename(path)
                db_image.path = path
                db_image.dataset_id = dataset_id
                db_image.width = pil_image.size[0]
                db_image.height = pil_image.size[1]
                db_image.regenerate_thumbnail = True
                db_image.uploaded_by = "System"
                db_image.save()
                image.close()
                pil_image.close()
            except OSError:
                return {'message': 'Can not read image from file'}, 500
            
            logger.info(f'Image post with filename: {db_image.file_name} and id {db_image.id}')
            return {'image_id': db_image.id}, 200
        else:
            return {'message': 'Upload not permitted with out key'}, 403

@api.route('/<int:image_id>')
class ImageId(Resource):

    @api.expect(image_download)
    #@login_required
    def get(self, image_id):
        """ Returns category by ID """
        args = image_download.parse_args()
        as_attachment = args.get('asAttachment')
        thumbnail = args.get('thumbnail')

        image = current_user.images.filter(id=image_id, deleted=False).first()

        if image is None:
            return {'success': False}, 400

        width = args.get('width')
        height = args.get('height')

        if not width:
            width = image.width
        if not height:
            height = image.height

        try:
            pil_image = image.open_thumbnail() if thumbnail else Image.open(image.path)
        except:
            pil_image = Image.open(image.path)    

        pil_image.thumbnail((width, height), Image.ANTIALIAS)
        image_io = io.BytesIO()
        pil_image = pil_image.convert("RGB")
        pil_image.save(image_io, "JPEG", quality=90)
        image_io.seek(0)

        return send_file(image_io, attachment_filename=image.file_name, as_attachment=as_attachment)

    # to do @sriram
    # uncomment below to delete from cs
    @login_required
    def delete(self, image_id):
        """ Deletes an image by ID """
        image = current_user.images.filter(id=image_id, deleted=False).first()
        if image is None:
            return {"message": "Invalid image id"}, 400

        if not current_user.can_delete(image):
            return {"message": "You do not have permission to download the image"}, 403

        image.update(set__deleted=True, set__deleted_date=datetime.datetime.now())
        return {"success": True}
    
    @api.expect(image_updates)
    def put(self, image_id):
        args = image_updates.parse_args()
        logger.info(f'args are, {args}')
        cs_annotating = args.get('cs_annotating')
        is_annotations_added = args.get('is_annotations_added')

        image = current_user.images.filter(id=image_id, deleted=False).first()
        if image is None:
            return {"message": "Invalid image id"}, 400
        
        if is_annotations_added:
            logger.info(f'current user: {current_user.username}')
            image.update(set__cs_annotating=cs_annotating, add_to_set__cs_annotated=current_user.username)
        else:
            logger.info(f'something wrong saving user')
            image.update(set__cs_annotating=cs_annotating)

        image_id = image.id
        image = current_user.images.filter(id=image_id, deleted=False).first()
        return{"message": "Updated image", "annotating": image.cs_annotating, "annotated by": image.cs_annotated}


@api.route('/copy/<int:from_id>/<int:to_id>/annotations')
class ImageCopyAnnotations(Resource):

    @api.expect(copy_annotations)
    @login_required
    def post(self, from_id, to_id):
        args = copy_annotations.parse_args()
        category_ids = args.get('category_ids')

        image_from = current_user.images.filter(id=from_id).first()
        image_to = current_user.images.filter(id=to_id).first()

        if image_from is None or image_to is None:
            return {'success': False, 'message': 'Invalid image ids'}, 400

        if image_from == image_to:
            return {'success': False, 'message': 'Cannot copy self'}, 400

        if image_from.width != image_to.width or image_from.height != image_to.height:
            return {'success': False, 'message': 'Image sizes do not match'}, 400

        if category_ids is None:
            category_ids = DatasetModel.objects(id=image_from.dataset_id).first().categories

        query = AnnotationModel.objects(
            image_id=image_from.id,
            category_id__in=category_ids,
            deleted=False
        )

        return {'annotations_created': image_to.copy_annotations(query)}


@api.route('/<int:image_id>/coco')
class ImageCoco(Resource):

    #@login_required
    def get(self, image_id):
        """ Returns coco of image and annotations """
        image = current_user.images.filter(id=image_id).exclude('deleted_date').first()
        
        if image is None:
            return {"message": "Invalid image ID"}, 400

        if not current_user.can_download(image):
            return {"message": "You do not have permission to download the images's annotations"}, 403

        return coco_util.get_image_coco(image_id)

@api.route('/<int:dataset_id>/<file_name>')
class FilenameId(Resource):

    def get(self, dataset_id, file_name):
        """returns image_id for file_name"""
        image = current_user.images.filter(dataset_id=dataset_id, file_name=file_name, deleted=False).first()
        if image:
            return {'image_id': image.id, 'dataset_id': dataset_id, 'file_name': file_name}, 200
        else:
            return {'message': 'image not found with the file_name'}, 404


@api.route('/<int:image_id>/instances')
class ImageIdInstances(Resource):

    @login_required
    def post(self, image_id):
        image = current_user.images.filter(id=image_id, deleted=False).first()
        if image is None:
            return {"message": "Invalid image ID"}, 400
        #project only on category_id and group by category_id and count
        im_instances = current_user.annotations.filter(image_id=image_id, deleted=False).aggregate(
            {
                "$project": {
                    "category_id": 1
                    }
            }, 
            {
                "$group": {
                    "_id": "$category_id", 
                    "count": {"$sum": 1}
                }
            }, 
            {
                "$group": {
                    "_id": 0, 
                    "data": {
                    "$push": {
                        "k": {"$convert": {"input": "$_id", "to": "string"}}, 
                        "v": "$count"
                        }
                    }
                }
            }, 
            {
                "$replaceRoot": {
                    "newRoot": {
                        "$arrayToObject": "$data"
                    }
                }
            }
        )

        im_instances = list(im_instances)
        if len(im_instances) > 0:
            im_instances = im_instances[0]
        else:
            im_instances = {}

        if image.instances != im_instances:
            image.update(set__instances=im_instances)
            return {'message': 'instances updated', 'instances': im_instances}, 200
        
        return {'message': 'Instances not changed', 'instances': im_instances}, 200

@api.route('/flag')
class ImageFlag(Resource):

    # @login_required
    @api.expect(flag_args)
    def post(self, image_id):

        args = flag_args.parse_args()
        image_id = args.get('image_id')
        is_flag = args.get('is_flagged')
        image = current_user.images.filter(id=image_id).first()
        if is_flag:
            image.update(add_to_set__cs_flagged_users=current_user.username)
        return {'success': True}
