
from database import (
    ImageModel,
    AnnotationModel,
    TaskModel,
    DatasetModel
)

from celery import shared_task
from ..socket import create_socket
from .thumbnails import thumbnail_generate_single_image

import os
from datetime import date, datetime, timedelta


@shared_task
#@task
def refresh_dataset(task_id, dataset_id, start_date, end_date):

    task = TaskModel.objects.get(id=task_id)
    dataset = DatasetModel.objects.get(id=dataset_id)

    task.update(status="PROGRESS")
    socket = create_socket()

    task.info(f"Scanning {dataset.name}")
    directory = dataset.directory
    prefix = dataset.images_prefix if dataset.images_prefix else ''
    task.info(f"Using prefix {prefix}")

    db_images = ImageModel.objects(dataset_id=dataset.id, file_name__gte=str(prefix+start_date), file_name__lte=str(prefix+end_date)).all()

    if db_images.count() == 0:
        task.info(f"No images found in the dataset")
        return

    start_date = datetime.strptime(start_date, '%Y%m%d').date()
    end_date = datetime.strptime(end_date, '%Y%m%d').date()

    delta = end_date - start_date

    count = 0
    youarehere = 0

    for i in range(delta.days + 1):
        progress = int(((youarehere)/db_images.count())*100)
        task.set_progress(progress, socket=socket)
        day = start_date + timedelta(days=i)
        day = day.strftime('%Y%m%d')
        task.info(f'{day}')
        day_images = ImageModel.objects(dataset_id=dataset.id, file_name__startswith=str(prefix+day)).all()
        task.info(f"{day} : {day_images.count()}")
        if day_images.count():
            # check if the directory exists
            if not os.path.exists(os.path.join(directory, day)):
                # create the directory
                os.makedirs(os.path.join(directory, day), exist_ok=True)
                task.info(f"Created directory {day}")
            else:
                task.info(f"Directory {day} already exists")
            fol_images = os.listdir(os.path.join(directory, day))
            
            if day_images.count() != len(fol_images):
                task.info(f"seems all images are not moved to {day} directory")
            else:
                task.info(f"All images are in {day} directory")
            
            for image in day_images:
                if image.file_name in fol_images:
                    path = os.path.join(directory, day, image.file_name)
                    if image.path != path:
                        image.update(path=path)
                    else:
                        pass
                if image.file_name not in fol_images:
                    task.info(f"Image {image.file_name} not found in directory {day}")
                    #check if image file exists in dataset.directory
                    if os.path.exists(os.path.join(directory, image.file_name)):
                        #move file to day directory
                        path = os.path.join(directory, day, image.file_name)
                        os.rename(os.path.join(directory, image.file_name), path)
                        image.update(path=path)
                        task.info(f"Image {image.file_name} moved to {day} directory")
                    elif os.path.exists(os.path.join(directory, day, image.file_name)):
                        pass
                    else:
                        image.delete() 
                youarehere += 1
                # youarehere += day_images.count()

    task.set_progress(100, socket=socket)


__all__ = ["refresh_dataset"]
