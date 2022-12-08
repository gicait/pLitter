# Prepare Nvidia Jetson Nano 4GB as CCTV camera for Floating Litter Detection

## Install OS and boot from TF card

If have original Nvidia Jetson Nano 4GB (b01) dev kit, download the [SDcard image](https://developer.nvidia.com/jetson-nano-sd-card-image), flash SDcard with the downloaded image. (Use [balena etcher](https://www.balena.io/etcher/) for flashing.) For more details, refer to [https://developer.nvidia.com/embedded/learn/get-started-jetson-nano-devkit](https://developer.nvidia.com/embedded/learn/get-started-jetson-nano-devkit).

If you have Alternative module, follow [steps from waveshare] https://www.waveshare.com/wiki/JETSON-NANO-DEV-KIT#Method_1:_Copy_the_system_directly_on_eMMC

## Install CUDA and PyTorch 

Get and update pip

    sudo apt update
    sudo apt install -y python3-pip
    pip3 install --upgrade pip

Install some dependencies

    sudo apt install -y libfreetype6-dev libjpeg-dev libopenblas-dev libopenmpi-dev libomp-dev zlib1g-dev

Check if CUDA available,

    nvcc -V

If CUDA not available, either use SDK manager from Nvida to install or run below. This step might be skipped if using board is official module.

    sudo apt install nvidia-jetpack

    echo $'export PATH="/usr/local/cuda/bin:${PATH}"' >> ~/.bashrc
    echo $'export LD_LIBRARY_PATH="/usr/local/cuda/lib64:${LD_LIBRARY_PATH}"' >> ~/.bashrc

Install PyTorch from below wheel

    wget https://nvidia.box.com/shared/static/fjtbno0vpo676a25cgvuqc1wty0fkkg6.whl -O torch-1.10.0-cp36-cp36m-linux_aarch64.whl
    pip3 install torch-1.10.0-cp36-cp36m-linux_aarch64.whl

    git clone --branch v0.11.1 https://github.com/pytorch/vision torchvision
    cd torchvision
    sudo python3 setup.py install
    cd ..

Test if PyTorch working with CUDA

    python3 -c 'import torch; torch.cuda.is_available()'


## Setting up pLitterCCTV + Yolov5 + StrongSort

Clone the cctv branch from plitter repo

    git clone -b cctv https://github.com/gicait/plitter
    cd plitter
    pip3 install -r requirements.txt

Update the details for camera configuration. Change the variable vavalues in [camera_config.env](camera_config.env) and [cctv_secret.env](cctv_secret.env), this information is necessary to uplaod the captured images and detections to the cloud.

Before you run the follow step, make surem a USB camera is plugged and device is connected to internet.

    sudo chmod +x start.sh
    ./start.sh

Check logs/ folder for logs. In case of erros follow the prompts, solve and run agian. If No errors your system is ready to deploy, add this to crontab to start at system boot up.

    @reboot path_to_plitter/start.sh


Refer to [components](components.md) for more information on list of components we use for building the CCTV station.