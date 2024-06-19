import datetime

from flask_restplus import Namespace, Resource
from flask_login import login_required, current_user
from flask import request

from ..util import query_util, coco_util, profile, thumbnails

from config import Config
from database import (
    ImageModel,
    DatasetModel,
    CategoryModel,
    AnnotationModel,
    SessionEvent
)
from mongoengine.queryset.visitor import Q

import logging
logger = logging.getLogger('gunicorn.error')

api = Namespace('annotator', description='Annotator related operations')

@api.route('/data')
class AnnotatorData(Resource):

    @profile
    @login_required
    def post(self):
        """
        Called when saving data from the annotator client
        """
        data = request.get_json(force=True)
        image = data.get('image')
        dataset = data.get('dataset')
        image_id = image.get('id')
        
        image_model = ImageModel.objects(id=image_id).first()

        if image_model is None:
            return {'success': False, 'message': 'Image does not exist'}, 400

        # Check if current user can access dataset
        db_dataset = current_user.datasets.filter(id=image_model.dataset_id).first()
        if dataset is None:
            return {'success': False, 'message': 'Could not find associated dataset'}
        
        db_dataset.update(annotate_url=dataset.get('annotate_url', ''))
        
        categories = CategoryModel.objects.all()
        annotations = AnnotationModel.objects(image_id=image_id)

        current_user.update(preferences=data.get('user', {}))

        annotated = False
        num_annotations = 0
        # Iterate every category passed in the data
        for category in data.get('categories', []):
            category_id = category.get('id')

            # Find corresponding category object in the database
            db_category = categories.filter(id=category_id).first()
            if db_category is None:
                continue

            category_update = {'color': category.get('color')}
            if current_user.can_edit(db_category):
                category_update['keypoint_edges'] = category.get('keypoint_edges', [])
                category_update['keypoint_labels'] = category.get('keypoint_labels', [])
                category_update['keypoint_colors'] = category.get('keypoint_colors', [])
            
            db_category.update(**category_update)

            # Iterate every annotation from the data annotations
            for annotation in category.get('annotations', []):
                counted = False
                # Find corresponding annotation object in database
                annotation_id = annotation.get('id')
                db_annotation = annotations.filter(id=annotation_id).first()

                if db_annotation is None:
                    continue

                # Paperjs objects are complex, so they will not always be passed. Therefor we update
                # the annotation twice, checking if the paperjs exists.

                # Update annotation in database
                sessions = []
                total_time = 0
                for session in annotation.get('sessions', []):
                    date = datetime.datetime.fromtimestamp(int(session.get('start')) / 1e3)
                    model = SessionEvent(
                        user=current_user.username,
                        created_at=date,
                        milliseconds=session.get('milliseconds'),
                        tools_used=session.get('tools')
                    )
                    total_time += session.get('milliseconds')
                    sessions.append(model)

                keypoints = annotation.get('keypoints', [])
                if keypoints:
                    counted = True

                db_annotation.update(
                    add_to_set__events=sessions,
                    inc__milliseconds=total_time,
                    set__isbbox=annotation.get('isbbox', False),
                    set__keypoints=keypoints,
                    set__metadata=annotation.get('metadata'),
                    set__color=annotation.get('color')
                )

                paperjs_object = annotation.get('compoundPath', [])

                # Update paperjs if it exists
                if len(paperjs_object) == 2:

                    width = db_annotation.width
                    height = db_annotation.height

                    # Generate coco formatted segmentation data
                    segmentation, area, bbox = coco_util.\
                        paperjs_to_coco(width, height, paperjs_object)

                    db_annotation.update(
                        set__segmentation=segmentation,
                        set__area=area,
                        set__isbbox=annotation.get('isbbox', False),
                        set__bbox=bbox,
                        set__paper_object=paperjs_object,
                    )

                    if area > 0:
                        counted = True

                if counted:
                    num_annotations += 1

        image_model.update(
            set__metadata=image.get('metadata', {}),
            set__annotated=(num_annotations > 0),
            set__category_ids=image.get('category_ids', []),
            set__regenerate_thumbnail=True,
            set__num_annotations=num_annotations
        )

        thumbnails.generate_thumbnail(image_model)

        return {"success": True}


@api.route('/data/<int:image_id>')
class AnnotatorId(Resource):

    @profile
    # @login_required
    # Add conditon if annotation to image (dataset) is_public?
    def get(self, image_id):
        """ Called when loading from the annotator client """
        image = ImageModel.objects(id=image_id)\
            .exclude('events').first()

        if image is None:
            return {'success': False, 'message': 'Could not load image'}, 400

        # until login condition set
        # dataset = current_user.datasets.filter(id=image.dataset_id).first()
        dataset = DatasetModel.objects(id=image.dataset_id).first()
        # add condition if dataset is_public?
        if dataset is None:
            return {'success': False, 'message': 'Could not find associated dataset'}, 400

        categories = CategoryModel.objects(deleted=False)\
            .in_bulk(dataset.categories).items()

        # Get next and previous image
        images = ImageModel.objects(dataset_id=dataset.id, deleted=False)
        pre = images.filter(file_name__lt=image.file_name).order_by('-file_name').first()
        nex = images.filter(file_name__gt=image.file_name).order_by('file_name').first()

        preferences = {}
        if not Config.LOGIN_DISABLED and current_user.is_authenticated:
            # change it after login_condition
            # print(current_user)
            # if current_user.username.:
            preferences = current_user.preferences

        # Generate data about the image to return to client
        data = {
            'image': query_util.fix_ids(image),
            'categories': [],
            'dataset': query_util.fix_ids(dataset),
            'preferences': preferences,
            'permissions': {
                'dataset': dataset.permissions(current_user),
                'image': image.permissions(current_user)
            }
        }

        data['image']['previous'] = pre.id if pre else None
        data['image']['next'] = nex.id if nex else None

        for category in categories:
            category = query_util.fix_ids(category[1])

            category_id = category.get('id')
            annotations = AnnotationModel.objects(image_id=image_id, category_id=category_id, deleted=False)\
                .exclude('events').all()

            category['show'] = True
            category['visualize'] = False
            category['annotations'] = [] if annotations is None else query_util.fix_ids(annotations)
            data.get('categories').append(category)

        return data

@api.route('/predictions')
class PredictionsData(Resource):

    @profile
    #@login_required
    def post(self):
        """
        Called when saving data from the edge predictor client
        """
        data = request.get_json(force=True)
        predictions = data.get('predictions', [])
        detections = data.get('detections', [])
        image_id = data.get('image_id')

        if predictions == []:
            predictions = detections
        # logger.info(f'detections: {data}')

        if not isinstance(image_id, int):
            return {'success': False, 'message': 'image_id is required'}, 404

        image_model = ImageModel.objects(id=image_id).first()

        if image_model is None:
            return {'success': False, 'message': 'Image does not exist'}, 404

        # Check if dataset exists
        db_dataset = DatasetModel.objects(id=image_model.dataset_id).first()
        if db_dataset is None:
            return {'success': False, 'message': 'Could not find associated dataset'}

        categories = CategoryModel.objects.all()
        annotations = AnnotationModel.objects(image_id=image_id)

        added_predictions = []
        added_categories = set()
        # Iterate every prediction from the data predictions
        # logger.info(f'predictions: {predictions}')
        for prediction in predictions:
            category_id = prediction.get('category_id', None)
            category_name = prediction.get('category', None)

            if category_name is not None:
                # logger.info(f'categegory name: {category_name}')
                #db_category = categories.filter(name=category_name).first()
                db_category = categories.filter(Q(name=category_name) | Q(othernames__in=category_name)).first()
                if db_category is not None:
                    category_id = db_category.id
                else:
                    category_id = 1
            else:
                # Find corresponding category object in the database
                db_category = categories.filter(id=category_id).first()

            if db_category is None:
                logger.info(f'db_category is None')
                continue

            segmentation = prediction.get('segmentation')
            bbox = prediction.get('bbox')
            isbbox = prediction.get('isbbox')
            area = prediction.get('area', None)
            track_id = prediction.get('track_id', None)
            if area is None:
                area = int(bbox[2]*bbox[3])
            try:
                # logger.info(f'creating annotation with {image_id, category_id, segmentation, bbox, isbbox, area, track_id}')
                annotation = AnnotationModel(
                    image_id=image_id,
                    category_id=category_id,
                    segmentation=segmentation,
                    bbox=bbox,
                    isbbox=isbbox,
                    area=area,
                    track_id=track_id
                )
                annotation.save()
                added_predictions.append({'success': True, 'annotation_id': annotation.id})
                added_categories.add(category_id)
            except (ValueError, TypeError) as e:
                added_predictions.append({'success': False, 'message': str(e)})

        num_annotations = len(added_predictions)
        image_model.thumbnail()

        image_model.update(
            set__annotated=(num_annotations > 0),
            set__category_ids=list(added_categories),
            set__regenerate_thumbnail=False,
            set__num_annotations=num_annotations,
            set__is_predicted_with=True
        )
        logger.info(f'{image_id, num_annotations}')

        return {"success": True, "annotations": added_predictions}, 200
