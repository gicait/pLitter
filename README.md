# pLitter - Plastic Litter identification and monitoring

pLitter-street is a standardized, deep learning friendly dataset and pre-trained model that can be used for detecting plastic litter at streets, road sides, and other outdoor areas. Additionally, all supplementary code related to this repository is also published here. *Example video showing plastic litter detection from our model (click on image to see the YouTube video) is shown below.*

<p align="center">
<a href="https://www.youtube.com/watch?v=REv0XEcWXVE" target="_blank">
<img src="https://img.youtube.com/vi/REv0XEcWXVE/0.jpg" alt="DL_Detection" width="50%"/>
</a>
</p>

pLitter-street helps to make predictions to detect theplastic litter in the images/videos and these detections are being used to map plastic litter distribution (as snapshot of plastic pollution) in the cities. *Example heat-map of a beach at Rayong(Thailand) is showing plastic litter distribution in a city is shown below.*

<p align="center">
<img src="./demo/figures/example_heatmap.PNG" alt="HeatMap" width="50%"/>
</p>

## Motivation

The Geoinformatics Center (GIC) of Asian Institute of Technology (AIT) partnered with the United Nations Environment Program (UNEP) for years, to form a network of volunteer cleanup teams to perform beach/river cleanup activities. Together UNEP and GIC worked for the CounterMEAUSRE project (https://countermeasure.asia/) in 2018, funded by the Government of Japan. The CounterMEASURE project works to identify sources and pathways of plastic pollution in river systems in Asia, particularly the Mekong and the Ganges. During the project implementation, project partners including local governments and universities collected thousands of images using GIC Mobile Application (Plastic Accumulation Hotspot Survey: https://arcg.is/1bDqbW) and it was not used to identify plastic litter. Therefore, our ultimate target is to build image recognition tools with modern machine learning techniques to quickly identify plastic litter in different scenes such as roadside, riverside, and beachside. We do believed that the outcome of this work can be used to inform policy decisions and actions to beat plastic pollution and ensure rivers are free of plastic waste.

## Our Approach

In the conventional sense, typical machine learning pipeline consisted of collecting data, annotating data, training, validation and prediction. This is a very successful pipeline for many problems such as face detection, character recognition, etc. But the problem with plastic litter is, simply it is trash, it can be seen in various types, shapes, forms, backgrounds etc. So, variations are too complex to capture in a single model with a single annotated dataset. So we believe, the solution for this is Active Learning. Our ultimate goal would be to go beyond domain specific plastic litter detections, and provide detection capabilities in a wide range of cities (universal plastic litter detector). Schematic diagram of active learning framework that we are using for plastic litter identification problem is shows in the below Figure. 

<p align="center">
<img src="./demo/figures/active_learning.PNG" alt="HeatMap" width="70%"/>
</p>


## Datasets

The datasets used in this repository can be downloaded from gdrive folder [pLitter-street](https://drive.google.com/drive/folders/165ZP5b9yU6Za8nfhdfGpoSyGFJTUpfiI?usp=sharing). Dataset contains RGB images, plastic litter annotations (JSON format same as COCO).

pLitter dataset contains images from following locations,
* Mekong river basin
* Pathumthani, Ubon Ratchathani, and Chiang Rai (Thailand)
* Can Tho (Vietnam)
* Hanwella & Mawanella (Sri Lanka)


*Note: We have used a open-source Annotator tool built from [COCO annotator](https://github.com/jsbroks/coco-annotator) for generation of bounding box annotations with the help of group of annotators. If you are planning to generate your own training data, it is an option*

## Pre-trained models

Models that are trained separately for each of the datasets, as well as model that is trained on combined dataset can be downloaded from following links,

<!---
| Talaad Thai | Rangsit | Ubon Ratchathani I | Chiang Rai I | Ubon Ratchathani II | Chiang Rai II | <ins>Combined Dataset</ins> |
| --- | --- | --- | --- | --- | --- | --- |
| [Docker](#) | [Docker](#) | Docker (ongoing) | Docker (ongoing) | Docker (ongoing) | Docker (ongoing) | [Docker](#) |
| [EDGE Model](#) | [EDGE Model](#) | EDGE Model (ongoing) | EDGE Model (ongoing) | EDGE Model (ongoing) | EDGE Model (ongoing) | [EDGE Model](#) |
| mAP = xx | mAP = xx | mAP = (ongoing) | mAP = (ongoing) | mAP = (ongoing) | mAP = (ongoing) | mAP = (ongoing) |
-->

| Model | mAP |
| --- | --- |
| Google AutoML\* [Cloud] | 0.77 |
| Faster RCNN (R101-FPN) | 0.67 |

*Note: \*These models are trained using [Google AutoML Vision tools](https://cloud.google.com/automl) in [Google Cloud Platform](https://cloud.google.com/).*

## Usage

Refer to [pLitter demo](/demo/pLitterStreet_demo.ipynb)

Also visit [pLitter pages](https://plitter.org) to look at the all initiatives of pLitter.

## ToDo

To deal with 360 images.

Train a light weight model for deploying with Rpi/jetson to fix it on garbage truck for real time prediction. 

## Citation

Use the below bibtex to cite us.

```BibTeX
@misc{pLitterStreet_2021,
  title={pLitter-street, Plastic Litter detection along the streets using deep learning},
  author={Sriram Reddy, Chatura Lavanga, Lakmal Deshapriya, and Sujit},
  year={2021},
  publisher={Github},
  howpublished={\url{https://github.com/gicait/pLitter/}},
}
```

## Developed by

[Geoinformatics Center](www.geoinfo.ait.ac.th) of [Asian Institute of Technology](www.ait.ac.th) and [Google](https://about.google/).

<!-- __Our Team__
* To be added
* ... -->

## Funding

[CounterMEASURE](https://countermeasure.asia/) project of [UN Environment Programme](https://www.unep.org/).
