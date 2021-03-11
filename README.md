# pLitter - Teaching Computers to Identify Plastic Litter

Identifies plastic litter from images using deep learning methods and generates heatmaps using predictions and exif metada.

## Motivation

Add some para about motivation

## Our Approach

In the conventional sense, typical machine learning pipeline consisted of collecting data, annotating data, training, validation and prediction. This was a very successful pipeline for decades for many problems such as face detection, character recognition, etc. But the problem with trash is, simply it is trash, it can be seen in various types, shapes, forms, backgrounds etc. So, variations are too complex to capture in a single model with a single annotated dataset. So we believe, the solution for this problem lies in a recently developed new branch of machine learning call Active Learning.

In essence, active learning brings collecting data, annotating data, training, validation and prediction into a single parallel framework, rather than sequential pipeline as in conventional machine learning projects. These have been successfully used in solving self-driving car problem which has wide range of possibilities as in our trash identification problem. Schematic diagram of active learning framework that we are proposing for trash identification problem is shows in the above Figure. 
As an example, a first neural network can be trained on a dataset sampled from a particular cleanup activity. Next, the whole process can move to a new location, with new sample data allowing the network to be adjusted to local domain using transfer learning. Eventually, such kind of active learning system can perform this process iteratively, adapting the neural network to each local domain.

**_Our Ultimate Goal_**

Our ultimate goal would be to go beyond domain specific trash detection, and provide detection capabilities in a wide range of domains including satellite images, drone images, mobile phone photos from streets / dump site, etc. We know, such kind of universal trash detector will be a challenging task that involves huge amount of data, large amount of manpower for annotation, huge computational resources. That is why we are looking for partnerships with government, private and non-profit organizations to achieve that ultimate goal of universal trash detector.


## Datasets

The datasets used in this repository can be downloaded from following links. Each link contains RGB images, plastic litter annotations (COCO format) and ReadMe file.

* [Talaad Thai](#)
* [Rangsit](#)
* Ubon Ratchathani I (ongoing)
* Chiang Rai I (ongoing)
* Ubon Ratchathani II (ongoing)
* Chiang Rai II (ongoing)

## Pre-trained models

Models that are trained separately for each of the datasets, as well as model that is trained on combined dataset can be downloaded from following links,

| Talaad Thai | Rangsit | Ubon Ratchathani I | Chiang Rai I | Ubon Ratchathani II | Chiang Rai II | <ins>Combined Dataset</ins> |
| --- | --- | --- | --- | --- | --- | --- |
| [Docker](#) | [Docker](#) | [Docker](#) | [Docker](#) | [Docker](#) | [Docker](#) | <ins>[Docker](#)</ins> |
| [EDGE Model](#) | [EDGE Model](#) | [EDGE Model](#) | [EDGE Model](#) | [EDGE Model](#) | [EDGE Model](#) | <ins>[EDGE Model](#)</ins> |

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
