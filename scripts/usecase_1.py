import datashader as ds
import pandas as pd
from bokeh.models import GeoJSONDataSource, LinearColorMapper, ColorBar
from bokeh.plotting import figure
from datashader.utils import export_image
import colorcet as cc
import matplotlib.pyplot as plt
import matplotlib.pyplot as plt
import pandas as pd
import geopandas as gpd
import numpy as np
import shapely

import pyproj
from pyproj import Transformer
from shapely.geometry import Polygon, MultiPolygon, shape, Point

import geoplot
from geoplot import utils
from geoplot import (
    pointplot,
    voronoi,
    kdeplot,
    polyplot,
    webmap,
    choropleth,
    cartogram,
    quadtree,
    sankey,
)
from geoplot.crs import AlbersEqualArea, WebMercator
import geoplot.crs as gcrs


from shapely.geometry import Polygon, MultiPolygon, shape, Point
from pyproj import Transformer
from matplotlib.cm import viridis
from matplotlib.cm import cividis


def convert_3D_2D(geometry):
    """
    Takes a GeoSeries of 3D Multi/Polygons (has_z) and returns a list of 2D Multi/Polygons

    Parameters
    ----------
    geometry (Polygon): Polygon in 3D LV95 LN02 coordinates

    Returns
    -------
    transformed_coords_list (list): List of Polygons transformed into 2D WGS84 coordinates

    """

    # Creating transformer object to transform coordinates from LV95 LN02 to WGS84
    transformer = Transformer.from_crs("epsg:2056", "epsg:4326")

    transformed_coords_list = []
    for p in geometry:
        if p.geom_type == "Polygon":
            lines = [
                transformer.transform(xy[0], xy[1]) for xy in list(p.exterior.coords)
            ]
            list_of_polygon_points = []

            # Correctly reswap the East and North Coordinate and transform into a point object
            for coords in lines:
                list_of_polygon_points.append(Point(coords[1], coords[0]))

            # Append the transformed Polygons to list
            transformed_coords_list.append(
                MultiPolygon([Polygon(list_of_polygon_points)])
            )

    return transformed_coords_list


def datashader_plot(just_basel, colormap, save=True, file_name=None, path_to_save=None):
    """
    Creating a datashader visualization for the traffic accidents of Basel/Switzerland

    Parameters
    ----------
    just_basel (Boolean): Deciding if Basel or Switerland dataset is used
    colormap (String): Provided options are "fire", "cividis" and "viridis"
    save (Boolean): Decides if the output should be saved
    file_name (String): Desired file name, when saving the plot
    path_to_save (String): Desired destination where visualization is saved

    Returns
    -------

    """

    # Setting the size of the visualization
    wid = 1000
    hgt = int(wid / 1.2)
    cvs = ds.Canvas(plot_width=wid, plot_height=hgt)

    # Decides which dataset should be plotted
    if just_basel:
        df = pd.read_csv("../data/straßenverkehrsunfaelle.csv", delimiter=";")
        agg = cvs.points(df, "Unfallort Ost-Koordinaten", "Unfallort Nord-Koordinaten")
    else:
        df = pd.read_csv(
            "../data/RoadTrafficAccidentLocations_clean.csv", delimiter=","
        )
        agg = cvs.points(df, "AccidentLocation_CHLV95_E", "AccidentLocation_CHLV95_N")

    # Choosing one of the following preceptually uniform sequential colormaps
    if colormap == "fire":
        img = ds.tf.shade(agg, cmap=cc.fire)
    elif colormap == "viridis":
        img = ds.tf.shade(agg, cmap=viridis)
    elif colormap == "cividis":
        img = ds.tf.shade(agg, cmap=cividis)

    img = ds.tf.set_background(img, "black")

    plt.imshow(img, aspect="auto")
    plt.show()

    if save:
        export_image(img, file_name, background="black", export_path=path_to_save)


def plotting_KDE_plot(boundary_map, df, colormap):
    """
    Creates a Kernel Density Estimation plot of Basel regarding the density of traffic accidents

    Parameters
    ----------
    boundary_map (Geopandas Dataframe): Contains the polygon object for the boundaries of Basel
    df (Geopandas Dataframe): Contains the geolocation points of interest (e.g. traffic accident locations)
    colormap (String): Allows to choose between colormaps (Recommended are viridis, cividis, Reds)

    Returns
    -------

    """

    # Creates the Kernel Density Plot based on the Geolocation Points given in the geometry column
    ax = geoplot.kdeplot(
        df, projection=gcrs.AlbersEqualArea(), shade=True, cmap=colormap, cbar=True
    )

    # Adds the boundary map to the existing KDE Plot
    geoplot.polyplot(boundary_map, ax=ax, zorder=0, projection=gcrs.AlbersEqualArea())

    plt.autoscale(False)

    # Add a title
    ax.set_title(
        "Kernel Density Estimation Plot for traffic accidents \n in Basel (2011 - 2023)",
        fontweight="bold",
    )
    plt.show()


def plotting_gridding_plot(boundary_map, df, colormap):
    """
    Creates a Heatmap-like visualization of Basel regarding the density of traffic accidents

    Parameters
    ----------
    boundary_map (Geopandas Dataframe): Contains the polygon object for the boundaries of Basel
    df (Geopandas Dataframe): Contains the geolocation points of interest (e.g. traffic accident locations)
    colormap (String): Allows to choose between colormaps (Recommended are viridis, cividis, Plasma)

    Returns
    -------

    Code is based on the Tutorial of James Brennan

    Link: https://james-brennan.github.io/posts/fast_gridding_geopandas/
    """
    # Drop unnecessary columns from Geopandas Dataframe
    gdf = df.drop(
        columns=[
            "accidentuid",
            "accidentsev",
            "accidentinv",
            "roadtype_de",
            "roadtype_fr",
            "roadtype_en",
            "accidentloc",
            "cantoncode",
            "municipalit",
            "accidentyea",
            "accidentmon",
            "accidentwee",
            "accidenthou",
            "accident_da",
            "roadtype",
        ]
    ).copy()

    # Defining the smallest bounding rectangle that encompasses all the geometries in the GeoDataFrame
    xmin, ymin, xmax, ymax = gdf.total_bounds
    # Defining the amount of cells (vertically & horizontally)
    n_cells = 75

    # Defining the size of the cells depending on the amount of the cells
    cell_size = (xmax - xmin) / n_cells

    # create the cells in a loop
    grid_cells = []
    for x0 in np.arange(xmin, xmax + cell_size, cell_size):
        for y0 in np.arange(ymin, ymax + cell_size, cell_size):
            # Define the bounds of each grid cell
            x1 = x0 - cell_size
            y1 = y0 + cell_size
            grid_cells.append(shapely.geometry.box(x0, y0, x1, y1))

    # Create a GeoDataFrame from the grid cells (WGS84 coordinates)
    cell = gpd.GeoDataFrame(grid_cells, columns=["geometry"], crs="EPSG:4326")

    # Perform a spatial join between the original GeoDataFrame (gdf) and the grid cells (cell)
    merged = gpd.sjoin(gdf, cell, how="left", predicate="within")

    # make a simple count variable that can be summed up
    merged["accidents"] = 1
    # Compute stats per grid cell -- aggregate fires to grid cells with dissolve
    dissolve = merged.dissolve(by="index_right", aggfunc="count")
    # put this into cell
    cell.loc[dissolve.index, "accidents"] = dissolve.accidents.values

    # Creating the plot with the gridlayout
    ax = cell.plot(
        column="accidents",
        figsize=(12, 8),
        cmap=colormap,
        vmax=72,
        edgecolor="grey",
        legend=True,
    )

    # Adding the boundary map to the plot
    boundary_map.plot(ax=ax, color="none", edgecolor="black")

    # Labeling the Axis
    ax.set_xlabel("Longitude Coordinates in WGS84", fontsize=12)
    ax.set_ylabel("Latitude Coordinates in WGS84", fontsize=12)

    plt.autoscale(False)

    # Add a title
    ax.set_title(
        "Heatmap like visualization of all traffic accidents from in Basel \n colorcoded by amount of accidents per square (2011 - 2023)",
        fontsize=16,
        fontweight="bold",
    )

    shape_filter.to_crs(cell.crs).plot(ax=ax, color="none", edgecolor="black")
    plt.show()


if __name__ == "__main__":
    # Calls the function for plotting the datashader visualizations
    datashader_plot(False, True, "test", "../images/")

    # Reads the shapefile containing the boundaries from all cantons
    shape = gpd.read_file(
        "../data/shapefiles_suisse/swissBOUNDARIES3D_1_4_TLM_KANTONSGEBIET.shp"
    )

    # Narrow done the Geopandas Dataframe to the Canton Basel-City
    shape_filter = shape[shape["NAME"].str.contains("Basel-Stadt")]

    # Transforming the given coordinates of the polygon into 2D WGS84 coordinates
    shape_filter.loc[:, "geometry"] = convert_3D_2D(shape_filter.geometry)

    # Reads the shapefile containing the traffic accident data
    df = gpd.read_file("../data/straßenverkehrsunfaelle_shp/100120.shp")

    # Calls the function for plotting the KDE plot visualization
    plotting_KDE_plot(shape_filter, df, "viridis")

    # Calls the function for plotting the Gridding plot visualization
    plotting_gridding_plot(shape_filter, df, "viridis")
