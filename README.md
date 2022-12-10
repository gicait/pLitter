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
Detailed list of components with figures are in [components.md](./components.md).

## Setup

Follow [Prepare_Nvidia_Jetson_Nano.md](./Prepare_Nvidia_Jetson_Nano.md) to install required libraried and setting up the camera.
