# GIST909 Capstone repository

This repository serves as a place for GIS professionals to download the script tool for their own use.

Abstract:

Data collection is often the most time-consuming part of a GIS research project. For a
viewshed analysis this involves identifying the coverage areas and selecting the exact grid
squares required by the study area. The goal of this tool is to save the end-user time by
automating the LiDAR download and viewshed calculation. This tool is run via the ArcGIS
Pro geoprocessing GUI through a custom python tool in a custom toolbox. This tool is
designed to retrieve LiDAR data from Pennsylvania Lidar Navigator hosted by Pennsylvania
Spatial Data Access. The tool generates a polygon around the target site which is used to
select Lidar aerial survey tiles that were imported via REST URL. These lidar aerial survey
tiles are then used to download their linked lidar aerial survey datasets, merged into one
universal lidar aerial survey dataset, and then used to run a geodesic viewshed. The
completion of this script produces a viewshed layer with automatic symbolization of green:
land visible up to eighty feet above ground level, blue: land visible from eighty feet to one
hundred twenty feet above ground level, and no fill color for anything above one hundred
twenty feet above ground level. Testing with this tool has resulted in successful viewshed
calculations with distances between observer and target features ranging from three statute
miles to twenty-six statute miles. With the tool successfully downloading and generating
viewsheds this tool allows end-users to multitask while this tool runs in the background,
effectively saving the end user time.
