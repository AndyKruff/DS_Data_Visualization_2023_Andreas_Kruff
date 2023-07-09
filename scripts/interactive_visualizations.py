import pandas as pd
from bokeh.models import Legend
import geopandas as gpd
import numpy as np
from bokeh.io import show
from bokeh.models import (
    ColorBar,
    GeoJSONDataSource,
    HoverTool,
    LinearColorMapper,
)
from bokeh.palettes import brewer
from bokeh.plotting import figure
from pyproj import Transformer
from shapely.geometry import Polygon, MultiPolygon, Point
from bokeh.palettes import Category20, Category20b, Category20c


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


def create_interactive_barplots(colormap="Category20c"):
    """
    Creates interactive stacked barplots with bokeh regarding the traffic accident situation in Basel

    Parameters
    ----------
    colormap (String): Oppportunities provided are Category20, Category20b and Category20c (Default: Category20c)

    Returns
    -------

    """

    # CSV was used because the Shapefile did not contain the descriptions for the accident types
    df_accidents = pd.read_csv("../data/straßenverkehrsunfaelle.csv", delimiter=";")

    # Aggregates the Accidenttype and the Accidentyear to calculate the amount of Accidents per Year per Type
    df_accidents_grouped = (
        df_accidents.groupby(["Unfalljahr", "Beschreibung zum Unfalltyp"])
        .size()
        .reset_index(name="counts")
    )

    # Creates a Dataframe that contains all possible combinations between accidentyear and accidentype
    all_combinations = pd.MultiIndex.from_product(
        [
            df_accidents["Unfalljahr"].unique(),
            df_accidents["Beschreibung zum Unfalltyp"].unique(),
        ],
        names=["Unfalljahr", "Beschreibung zum Unfalltyp"],
    )
    all_combinations_df = pd.DataFrame(index=all_combinations).reset_index()

    # Merging the dataframes to ensure that accidentyear-accidentype combinations don't get lost, when their group size was zero
    df_accidents_grouped = pd.merge(
        all_combinations_df,
        df_accidents_grouped,
        on=["Unfalljahr", "Beschreibung zum Unfalltyp"],
        how="left",
    ).fillna(0)
    df_accidents_grouped = df_accidents_grouped.reset_index(drop=True)

    df_accidents_grouped = df_accidents_grouped.sort_values(
        ["Unfalljahr", "Beschreibung zum Unfalltyp"]
    )
    df_accidents_grouped = df_accidents_grouped.reset_index(drop=True)
    df_group_reformated = (
        df_accidents_grouped.groupby("Beschreibung zum Unfalltyp")["counts"]
        .apply(list)
        .reset_index(name="counts_list")
    )

    # Remap the Accidentype descriptions into english
    mapping = {
        "Schleuder- oder Selbstunfall": "Accident with skidding or self-accident",
        "Überholunfall oder Fahrstreifenwechsel": "Accident when overtaking or changing lanes",
        "Auffahrunfall": "Accident with rear-end collision",
        "Abbiegeunfall": "Accident when turning left or right",
        "Einbiegeunfall": "Accident when turning-into main road",
        "Andere": "Other",
        "Überqueren der Fahrbahn": "Accident when crossing the lane(s)",
        "Frontalkollision": "Accident with head-on collision",
        "Parkierunfall": "Accident when parking",
        "Fussgängerunfall": "Accident involving pedestrian(s)",
        "Tierunfall": "Accident involving animal(s)",
    }  # Mapping der Abkürzungen zu den Beschreibungen

    df_group_reformated["Beschreibung zum Unfalltyp"] = df_accidents_grouped[
        "Beschreibung zum Unfalltyp"
    ].replace(mapping)

    year = df_accidents_grouped["Unfalljahr"].unique()
    year = list(map(str, year))
    typ = df_group_reformated["Beschreibung zum Unfalltyp"].unique()
    data = {"years": list(year)}
    for i, j in df_group_reformated.iterrows():
        data[str(j["Beschreibung zum Unfalltyp"])] = j["counts_list"]

    if colormap == "Category20":
        color_palette = Category20[len(typ)]
    elif colormap == "Category20b":
        color_palette = Category20b[len(typ)]
    elif colormap == "Category20c":
        color_palette = Category20c[len(typ)]

    # Creating the stacked barplot
    p = figure(
        x_range=year,
        title="Amount of accidents per type per year in Basel-City",
        toolbar_location=None,
        tools="hover",
        tooltips="$name: @$name",
        width=800,
    )

    renderers = p.vbar_stack(
        typ, x="years", width=0.9, color=color_palette, source=data
    )
    p.y_range.start = 0
    p.x_range.range_padding = 0.1
    p.xgrid.grid_line_color = None
    p.axis.minor_tick_line_color = None
    p.outline_line_color = None
    # p.legend.location = "top_right"
    # p.legend.orientation = "vertical"
    p.xaxis.axis_label = "Year"
    p.yaxis.axis_label = "Amount of Accidents per Year"
    legend = Legend(
        items=[(t, [r]) for t, r in zip(typ, renderers)][::-1],
        location="top_right",
        spacing=5,
    )
    p.add_layout(legend, "right")

    show(p)


def create_choropleth_map(year_to_display, colormap="Viridis", just_basel=True):
    """
    Creates a choropleth map of either the Switzerland or the canton Basel-City

    Parameters
    ----------
    just_basel (Boolean): Should the choropleth map be created based on the city of Basel or the Switzerland
    colormap (String): Opportunities provided are cividis, viridis and Reds (Default: viridis)
    year_to_display (Integer): Accidents of that year will be displayed in the choropleth map

    Returns
    -------

    """

    # Decides if using the Basel-City dataset or the Switzerland dataset

    if just_basel:
        shape = gpd.read_file("../data/shapefiles_gemeinden_basel/100017.shp")
        data_accidents = gpd.read_file("../data/straßenverkehrsunfaelle_shp/100120.shp")
    else:
        shape = gpd.read_file(
            "../data/shapefiles_suisse/swissBOUNDARIES3D_1_4_TLM_KANTONSGEBIET.shp"
        )
        df = pd.read_csv(
            "../data/RoadTrafficAccidentLocations_clean.csv", delimiter=","
        )

    # Remaps the Municipality/Canton codes to be able to merge the dataframes with the boundary maps by name
    if just_basel:
        conditions = [
            (data_accidents["municipalit"] == "2701"),
            (data_accidents["municipalit"] == "2702"),
            (data_accidents["municipalit"] == "2703"),
        ]

        # create a list of the values we want to assign for each condition
        values = ["Basel", "Bettingen", "Riehen"]

        # create a new column and use np.select to assign values to it using our lists as arguments
        data_accidents["name"] = np.select(conditions, values)
    else:
        conditions = [
            (df["CantonCode"] == "ZH"),
            (df["CantonCode"] == "GE"),
            (df["CantonCode"] == "BE"),
            (df["CantonCode"] == "BS"),
            (df["CantonCode"] == "TI"),
            (df["CantonCode"] == "VS"),
            (df["CantonCode"] == "VD"),
            (df["CantonCode"] == "GR"),
            (df["CantonCode"] == "LU"),
            (df["CantonCode"] == "TG"),
            (df["CantonCode"] == "FR"),
            (df["CantonCode"] == "SG"),
            (df["CantonCode"] == "SO"),
            (df["CantonCode"] == "AG"),
            (df["CantonCode"] == "SZ"),
            (df["CantonCode"] == "OW"),
            (df["CantonCode"] == "AR"),
            (df["CantonCode"] == "ZG"),
            (df["CantonCode"] == "JU"),
            (df["CantonCode"] == "BL"),
            (df["CantonCode"] == "NE"),
            (df["CantonCode"] == "AI"),
            (df["CantonCode"] == "NW"),
            (df["CantonCode"] == "SH"),
            (df["CantonCode"] == "GL"),
            (df["CantonCode"] == "UR"),
        ]

        # create a list of the values we want to assign for each condition
        values = [
            "Zürich",
            "Genève",
            "Bern",
            "Basel-Stadt",
            "Ticino",
            "Valais",
            "Vaud",
            "Graubünden",
            "Luzern",
            "Thurgau",
            "Fribourg",
            "St. Gallen",
            "Solothurn",
            "Aargau",
            "Schwyz",
            "Obwalden",
            "Appenzell Ausserrhoden",
            "Zug",
            "Jura",
            "Basel-Landschaft",
            "Neuchâtel",
            "Appenzell Innerrhoden",
            "Nidwalden",
            "Schaffhausen",
            "Glarus",
            "Uri",
        ]

        # create a new column and use np.select to assign values to it using our lists as arguments
        df["name"] = np.select(conditions, values)

    if just_basel:
        # Calculates the amount of accidents per year and per roadtype

        data_accidents = (
            data_accidents.groupby(["name", "accidentyea", "roadtype_en"])[
                ["accidentyea", "roadtype_en"]
            ]
            .size()
            .reset_index(name="counts")
        )

        # Reformates the dataframe by using the roadtypes as new columns
        pivot_df = data_accidents.pivot_table(
            index=["name", "accidentyea"],
            columns="roadtype_en",
            values="counts",
            aggfunc="sum",
        ).reset_index()

        # Fill NaN values with zero
        pivot_df = pivot_df.fillna(0)

        # Merge the boundary map and the reformated Dataframe by name (municipality name)
        merge_df = shape.merge(pivot_df, left_on="name", right_on="name")

        # Dropping unnecessary columns
        merge_df = merge_df.drop(
            columns=[
                "entstehung",
                "ortschaft",
                "status",
                "status_txt",
                "inaenderun",
                "inaenderu1",
                "r1_objid",
                "r1_nbident",
                "r1_identif",
                "r1_beschre",
                "r1_gueltig",
                "r1_guelti1",
                "r1_guelti2",
            ]
        )

        # Calculating the total amount of accidents per year and per municipality
        merge_df["Total"] = merge_df.apply(
            lambda x: x["Minor road"]
            + x["Motorway"]
            + x["Motorway side installation"]
            + x["Other"]
            + x["Principal road"],
            axis=1,
        )
    else:
        # Calculates the amount of accidents per year and per roadtype

        data_accidents = (
            df.groupby(["name", "AccidentYear", "RoadType_en"])[
                ["AccidentYear", "RoadType_en"]
            ]
            .size()
            .reset_index(name="counts")
        )
        # Reformates the dataframe by using the roadtypes as new columns

        pivot_df = data_accidents.pivot_table(
            index=["name", "AccidentYear"],
            columns="RoadType_en",
            values="counts",
            aggfunc="sum",
        ).reset_index()

        # Fill NaN values with zero

        pivot_df = pivot_df.fillna(0)

        # Merge the boundary map and the reformated Dataframe by name (Canton name)

        merge_df = shape.merge(pivot_df, left_on="NAME", right_on="name")

        # Calculating the total amount of accidents per year and per canton
        merge_df["Total"] = merge_df.apply(
            lambda x: x["Minor road"]
            + x["Motorway"]
            + x["Motorway side installation"]
            + x["Other"]
            + x["Principal road"],
            axis=1,
        )

        # Dropping unnecessary columns
        merge_df = merge_df[
            [
                "name",
                "geometry",
                "AccidentYear",
                "Expressway",
                "Minor road",
                "Motorway",
                "Motorway side installation",
                "Other",
                "Principal road",
                "Total",
            ]
        ]

    merge_df = merge_df.to_crs(epsg=4326)

    # Reformat the dataframe into a GeoJson
    geosource = GeoJSONDataSource(geojson=merge_df.to_json())

    # Define color palettes
    if just_basel:
        geosource = GeoJSONDataSource(
            geojson=merge_df[merge_df["accidentyea"] == str(year_to_display)].to_json()
        )
    else:
        geosource = GeoJSONDataSource(
            geojson=merge_df[merge_df["AccidentYear"] == year_to_display].to_json()
        )

    if colormap == "Reds":
        palette = brewer["Reds"]
    elif colormap == "viridis" or colormap == "Viridis":
        from bokeh.palettes import Viridis256

        palette = Viridis256
    elif colormap == "cividis" or colormap == "cividis":
        from bokeh.palettes import Cividis256

        palette = Cividis256

    # reverse order of colors so higher values have darker colors
    palette = palette[::-1]
    # Instantiate LinearColorMapper that linearly maps numbers in a range, into a sequence of colors.
    color_mapper = LinearColorMapper(palette=palette, low=0, high=1000)

    # Create color bar.
    color_bar = ColorBar(color_mapper=color_mapper)

    # Create figure object.
    if just_basel:
        p = figure(
            title=f"Total Car Accidents in the three municipalities \n of Basel, {year_to_display}",
            height=600,
            width=950,
            toolbar_location="below",
            tools="pan, wheel_zoom, box_zoom, reset",
        )
    else:
        p = figure(
            title=f"Comparing the total amount of accidents between the cantons \n of Switzerland, {year_to_display}",
            height=600,
            width=950,
            toolbar_location="below",
            tools="pan, wheel_zoom, box_zoom, reset",
        )

    # Setting multiple appearance options for the plot
    p.xgrid.grid_line_color = None
    p.ygrid.grid_line_color = None
    p.title.align = "center"
    p.title.text_align = "center"

    p.title.text_font_size = "25px"
    p.yaxis.axis_label = "Latitude Coordinates in WGS84"
    p.xaxis.axis_label = "Longitude Coordinates in WGS84"

    # Add patch renderer to figure.
    states = p.patches(
        "xs",
        "ys",
        source=geosource,
        fill_color={"field": "Total", "transform": color_mapper},
        line_color="gray",
        line_width=0.25,
        fill_alpha=1,
    )
    # Create hover tool
    if just_basel:
        p.add_tools(
            HoverTool(
                renderers=[states],
                tooltips=[
                    ("Municipality", "@name"),
                    ("Total Accidents", "@Total"),
                    ("Minor road", "@{Minor road}"),
                    ("Motorway", "@Motorway"),
                    ("Motorway side installation", "@{Motorway side installation}"),
                    ("Other", "@Other"),
                    ("Principal road", "@{Principal road}"),
                ],
            )
        )
    else:
        p.add_tools(
            HoverTool(
                renderers=[states],
                tooltips=[
                    ("Canton", "@name"),
                    ("Total Accidents", "@Total"),
                    ("Minor road", "@{Minor road}"),
                    ("Motorway", "@Motorway"),
                    ("Motorway side installation", "@{Motorway side installation}"),
                    ("Other", "@Other"),
                    ("Principal road", "@{Principal road}"),
                ],
            )
        )
    p.add_layout(color_bar, "right")

    show(p)


if __name__ == "__main__":
    # Creates the interactive stacked barplot
    create_interactive_barplots(colormap="Category20c")
    # Creates the interactive choropleth map
    create_choropleth_map(just_basel=False, year_to_display=2012, colormap="viridis")
