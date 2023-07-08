# Project: Visualization of the traffic situation in the “SmartCity” Basel

**Informations**  
Module: DVI - Data Viszalization 
Lecturer: Prof. Dr. Konrad Förstner, Muhammad Elhossary  
Participant: Andreas Kruff  
Matrikel-Nr: 11135772
  
```
Visualization of the traffic situation in the “SmartCity” Basel
```
**Keywords:** Data Visualization

## Setup the Environment:

For the creation of the enviroment I recommend to use a Conda Enviroment, due to dependenciy problems regarding geopandas, geoplot, cartopy and pyproj. Therefore the Repository provides the enviroment.yml for installing the necessary dependencies.

For creating the environment use:

```shell 

conda env create -f environment.yml

```
 

## Description:

This repository was created as part of the examination of the module Data Visualization 2023 (Master Digital Science) and contains the used code, part of the used datasets and the project presentation and related images from this project.

#### Structure of this Repository
* `data\`: Datasets used for the visualizations
* `project_presentation\`: Powerpoint presentation regarding the project
* `scripts\`: Code implementation of the underlying visualizations
* `images\`: Exemplary images from the visualizations, that were made for the project

#### Description of the python files
| Filename                    | Description                                                                                                                                                         |
| --------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `./scripts/usecase_1.py` | Contains the code for the three different approaches for the identification of potential hotspots |
| `./scripts/usecase_2.py` | Contains the code for the lineplot visualizations of the traffic noise in Basel-City |
| `./scripts/interactive_visualizations.py` | Contains the code for the interactive bokeh visualizations |


## Impressions:

| ![Bild 1](./images/heatmap_vis.png) | ![Bild 2](./images/kdeplot_basel.png) |
| -------------------- | -------------------- |
| ![Bild 3](./images/datashader_basel.png) | ![Bild 4](./images/choropleth_switzerland.PNG) |

## References:

General Data Source Datenportal Basel:
https://data.bs.ch/explore/?sort=modified

Used datasets:
- [Road Traffic Accidents](https://data.bs.ch/explore/dataset/100120/table/?disjunctive.accidenttype_de&disjunctive.accidentseveritycategory_de&disjunctive.roadtype_de&disjunctive.accidentweekday_de&sort=accident_date)
- [Traffic Noise](https://data.bs.ch/explore/dataset/100087/table/?sort=timestamp) (not provided in the Repo, because of the size)
- [Boundaries of the Municipalities of Basel](https://data.bs.ch/explore/dataset/100017/table/)

General Data Source GEO.ADMIN.CH:
https://data.geo.admin.ch/

Used datasets:
- [All accidents with personal injury (Switzerland)](https://data.geo.admin.ch/ch.astra.unfaelle-personenschaeden_alle/)

General Datasource swisstopo:
https://www.swisstopo.admin.ch/de/geodata/landscape/boundaries3d.html

- [Download Link to the latest boundary map of switzerland](https://data.geo.admin.ch/ch.swisstopo.swissboundaries3d/swissboundaries3d_2023-01/swissboundaries3d_2023-01_2056_5728.shp.zip)
 