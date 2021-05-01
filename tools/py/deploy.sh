# https://cloud.google.com/vision/automl/docs/containers-gcs-tutorial?hl=en_US
if [[ $(which docker) && $(docker --version) ]]; then
    echo "Found docker, pulling gcloud-container-1.14.0:latest"

    export CPU_DOCKER_GCR_PATH=gcr.io/cloud-devrel-public-resources/gcloud-container-1.14.0:latest
    sudo docker pull ${CPU_DOCKER_GCR_PATH}
    export CONTAINER_NAME=automl_edge_plitter
    export PORT=8501
    if ["$1" == ""]; then
        echo "loading model from ${1}"
        echo "please absolute path to saved model, for default look at models folder"
      else
        export YOUR_MODEL_PATH=$1
        sudo docker run --rm --name ${CONTAINER_NAME} -p ${PORT}:8501 -v ${YOUR_MODEL_PATH}:/tmp/mounted_model/0001 -t ${CPU_DOCKER_GCR_PATH}
    fi
  else
    echo "Install docker to continue deploiyng the model."
fi
