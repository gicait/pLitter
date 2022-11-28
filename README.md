# pLitterCam - An IoT style camera for plastic debris (floating) detection 

This tool is used to prepare a standalone CCTV type camera system using Nvidia Jetson Nano or any other Single board computer.


## How it works

There are two main tasks running after boot,
1. Capture the images 
2. Upload the images to cloud

camera starts capturing images with a selected interval, detects the objects (floating plastics) in the image, and upload the image and detections to the cloud.

## Required Hardware

Jetson Nano 4GB or
USB camera or CSI camera 
Detailed component diagram is given below.

## Setup

Follow steps.txt to install required libraried and setting up the camera.

Create a file called "camera_config.env", here we save the all the details for the camera such as camera resolution, interval to save an image.

```
frame_height=1920
frame_width=1080
images_prefix=''
interval=60
new_weights=true
gitpull=false
send_empty=true
silce_width=640
slice_height=640
weights_url=https://github.com/gicait/pLitter/releases/download/v0.0.1/pLitterFloat_1216_x_1216_yolov5s.pt
```
Paste the above and chnage the values as desired.

Create an another file , here we save the information of cloud api and secret keys if images are needed to upload to cloud. Below is for an example, it may change with your cloud API.
```
url=API address here
id=Number
token=strongtoken
```
Next, add the start.sh to crontab to start the tasks at boot.

> @reboot sleep 5 && path_to_project/plitter/start.sh
