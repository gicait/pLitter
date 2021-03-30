import os
import base64
import io
import json
import tensorflow as tf
import requests
import cv2
import csv

class inference():

    def predict_from_cloud(self, image_path):
        url = 'http://203.159.29.51:5005/predict'
        image = {'image': open(image_path, 'rb')}
        response = requests.post(url, files=image)
        res = response.json()
        predictions = res['predictions']
        return predictions
    
    def load_local_model(self, model_path):
        loaded = tf.saved_model.load(export_dir=model_path)
        self.infer = loaded.signatures["serving_default"]
    
    def predict_from_local(self, path):
        if type(path) == str:
            img = cv2.imread(path)
            flag, bts = cv2.imencode('.jpg', img)
            inp = [bts[:,0].tobytes()]
            out = self.infer(key=tf.constant('something_unique'), image_bytes=tf.constant(inp))
        else:
            # change condition to check image
            flag, bts = cv2.imencode('.jpg', path)
            inp = [bts[:,0].tobytes()]
            out = self.infer(key=tf.constant('something_unique'), image_bytes=tf.constant(inp))
        return out

    def predict_from_container(self, image_file_path, image_key, port_number=8501):
        """Sends a prediction request to TFServing docker container REST API.

        Args:
            image_file_path: Path to a local image for the prediction request.
            image_key: Your chosen string key to identify the given image.
            port_number: The port number on your device to accept REST API calls.
        Returns:
            The response of the prediction request.
        """
        with io.open(image_file_path, 'rb') as image_file:
            encoded_image = base64.b64encode(image_file.read()).decode('utf-8')

        # The example here only shows prediction with one image. You can extend it
        # to predict with a batch of images indicated by different keys, which can
        # make sure that the responses corresponding to the given image.
        instances = {
                'instances': [
                        {'image_bytes': {'b64': str(encoded_image)},
                         'key': image_key}
                ]
        }

        # This example shows sending requests in the same server that you start
        # docker containers. If you would like to send requests to other servers,
        # please change localhost to IP of other servers.
        url = 'http://localhost:{}/v1/models/default:predict'.format(port_number)

        try:
            response = requests.post(url, data=json.dumps(instances))
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            raise SystemExit(err)
        
        res = response.json()
        predictions = res['predictions']
        return predictions

    def predict_and_save_to_csv(self, dir_path, thresould=0.35):
        with open(os.path.join(dir_path, os.path.basename(dir_path)+'local_predictions.csv'), 'w') as csvfile:
            csvwriter = csv.writer(csvfile)
            for image in sorted(os.listdir(dir_path)):
                if image.endswith(('.png', '.jpg')):
                    img = cv2.imread(os.path.join(dir_path, image))
                    flag, bts = cv2.imencode('.jpg', img)
                    inp = [bts[:,0].tobytes()]
                    out = self.infer(key=tf.constant('something_unique'), image_bytes=tf.constant(inp))
                    for i in range(int(out['num_detections'].numpy()[0])):
                        if out['detection_scores'].numpy()[0][i] >= thresould:
                            row = []
                            row.append(image)
                            row.append(out['detection_classes_as_text'].numpy()[0][i].decode('utf-8'))
                            row.append(out['detection_scores'].numpy()[0][i])
                            row.extend(out['detection_boxes'].numpy()[0][i])
                            csvwriter.writerow(row)
        csvfile.close()




# def container_predict(image_file_path, image_key, port_number=8501):
#     """Sends a prediction request to TFServing docker container REST API.

#     Args:
#         image_file_path: Path to a local image for the prediction request.
#         image_key: Your chosen string key to identify the given image.
#         port_number: The port number on your device to accept REST API calls.
#     Returns:
#         The response of the prediction request.
#     """

#     with io.open(image_file_path, 'rb') as image_file:
#         encoded_image = base64.b64encode(image_file.read()).decode('utf-8')

#     # The example here only shows prediction with one image. You can extend it
#     # to predict with a batch of images indicated by different keys, which can
#     # make sure that the responses corresponding to the given image.
#     instances = {
#             'instances': [
#                     {'image_bytes': {'b64': str(encoded_image)},
#                      'key': image_key}
#             ]
#     }

#     # This example shows sending requests in the same server that you start
#     # docker containers. If you would like to send requests to other servers,
#     # please change localhost to IP of other servers.
#     url = 'http://localhost:{}/v1/models/default:predict'.format(port_number)

#     response = requests.post(url, data=json.dumps(instances))
#     print(response.json())

# container_predict('/media/sriram/ALearning/CS/Thalat Thai/GX014430 003.jpg', '/media/sriram/ALearning/CS/Thalat Thai/GX014430 003.jpg')