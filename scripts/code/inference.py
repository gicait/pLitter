import base64
import io
import json

import requests

class inference():

    def predict_from_cloud(self, image_path):
        url = 'http://203.159.29.51:5005/predict'
        image = {'image': open(image_path, 'rb')}
        response = requests.post(url, files=image)
        res = response.json()
        predictions = res['predictions']
        return predictions
    
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