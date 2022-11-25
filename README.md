# pLitterStreet - Plastic Litter detection along the streets and roadsides

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

Visit https://plitter.org/street or https://gicait.github.io/pLitter/street/ to find more about plitter street mapping.

## Dataset

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
  author={Sriram Reddy, Chatura Lavanga, Lakmal Deshapriya, Dan Tran, Kavinda Gunasekara, and Sujit},
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
