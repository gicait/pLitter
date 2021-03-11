# pLitter - Teaching Computers to Identify Plastic Litter

pLitter is a standardized, deep learning friendly data set and pre-trained models that can be used for detecting road-size plastic litter. Aditionally, all suplimentary codes related to this repository is also published here.

_Note: This is a preliminary release and more data from more cities will be added in future._

## Motivation

Add some para about motivation

## Our Approach

In the conventional sense, typical machine learning pipeline consisted of collecting data, annotating data, training, validation and prediction. This is a very successful pipeline for decades for many problems such as face detection, character recognition, etc. But the problem with trash is, simply it is trash, it can be seen in various types, shapes, forms, backgrounds etc. So, variations are too complex to capture in a single model with a single annotated dataset. So we believe, the solution for this is inActive Learning.

In essence, active learning brings collecting data, annotating data, training, validation and prediction into a single parallel framework, rather than sequential pipeline as in conventional machine learning projects. Schematic diagram of active learning framework that we are proposing for trash identification problem is shows in the below Figure. 


**_Our Ultimate Goal:_** Our ultimate goal would be to go beyond domain specific trash detection, and provide detection capabilities in a wide range of cities (universal plastic litter detector)


## Datasets

The datasets used in this repository can be downloaded from following links. Each link contains RGB images, plastic litter annotations (COCO format) and ReadMe file.

* [Talaad Thai](#)
* [Rangsit](#)
* Ubon Ratchathani I (ongoing)
* Chiang Rai I (ongoing)
* Ubon Ratchathani II (ongoing)
* Chiang Rai II (ongoing)

*Note: We have used [COCO Annotator](https://github.com/jsbroks/coco-annotator) for generation of bounding box annotations. If you are planning to generate your own training data, it is an one option*

## Pre-trained models

Models that are trained separately for each of the datasets, as well as model that is trained on combined dataset can be downloaded from following links,

| Talaad Thai | Rangsit | Ubon Ratchathani I | Chiang Rai I | Ubon Ratchathani II | Chiang Rai II | <ins>Combined Dataset</ins> |
| --- | --- | --- | --- | --- | --- | --- |
| [Docker](#) | [Docker](#) | Docker (ongoing) | Docker (ongoing) | Docker (ongoing) | Docker (ongoing) | <ins>[Docker](#)</ins> |
| [EDGE Model](#) | [EDGE Model](#) | EDGE Model (ongoing) | EDGE Model (ongoing) | EDGE Model (ongoing) | EDGE Model (ongoing) | <ins>[EDGE Model](#)</ins> |

*Note: These models are trained using Google [AutoML Vision tool](https://cloud.google.com/automl) in [Google Cloud Platform](https://cloud.google.com/)*

## Usage

Please add some technical details about basic use of repository.

## Documentation
Documentation is located in "docs" folder.

## Citation

Use this bibtex to cite us.
```
@misc{pLitter_2021,
  title={pLitter - Teaching Computers to Identify Plastic Litter},
  author={We have to add names here},
  year={2021},
  publisher={Github},
  journal={GitHub repository},
  howpublished={\url{https://github.com/gicait/pLitter/}},
}
```

## Developed by

[Geoinformatics Center](www.geoinfo.ait.ac.th) of [Asian Institute of Technology](www.ait.ac.th) and [Google Sustainability Team](https://sustainability.google/).

## Funding

[CounterMEASURE](https://countermeasure.asia/) project of [UN Environment Programme](https://www.unep.org/).
