A tool to detect the plastics in the images/videos and plot the resukts in the map.

If a folder of images is given, program will loop through the images, to predict the plastics, extracts the GPS location and store them to a file.

If a folder of videos given, it expects a telemetry file (gpx or csv) for gps information, and predticted plastics will be associated with GPS information and stored to a file.


# Steps

street = pStreet('data_folder')
or
street = pStreet()
street.load('data_folder')

It finds images and videos in that folder, check if the GPS information available from them.

street.predict('model', 'weights')
                'yolov5', 'yolov5l.pt'
                'tflite', 'model.tflite'

street.export()


