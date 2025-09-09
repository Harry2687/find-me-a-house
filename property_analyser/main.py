import marimo

__generated_with = "0.15.2"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    from dotenv import load_dotenv

    import os
    import polars as pl
    import folium

    from mapping_functions import (
        gmaps,
        next_weekday_at_830,
        get_nearby,
        plot_nearby,
    )

    load_dotenv()
    return folium, get_nearby, gmaps, mo, next_weekday_at_830, os, plot_nearby


@app.cell
def _(mo, os):
    # Define Marimo input objects
    address = mo.ui.text_area(
        value=os.getenv("MY_ADDRESS"), placeholder="Enter property address..."
    )
    workplace = mo.ui.text_area(
        value=os.getenv("WORK"), placeholder="Enter work address..."
    )
    return address, workplace


@app.cell
def _(address, mo, workplace):
    mo.md(
        f"""
    Address: {address}\n
    Work Address: {workplace}
    """
    )
    return


@app.cell
def _(address, gmaps):
    geocode_result = gmaps.geocode(address.value)

    location = geocode_result[0]["geometry"]["location"]
    origin_lat = location["lat"]
    origin_lng = location["lng"]
    origin = (origin_lat, origin_lng)

    formatted_address = geocode_result[0]["formatted_address"]
    location_id = geocode_result[0]["place_id"]
    return formatted_address, origin_lat, origin_lng


@app.cell
def _(formatted_address, mo):
    mo.md(f"""Address search result: {formatted_address}""")
    return


@app.cell
def _(gmaps, next_weekday_at_830, origin_lat, origin_lng, workplace):
    work_directions_pt = gmaps.directions(
        origin=(origin_lat, origin_lng),
        destination=workplace.value,
        mode="transit",
        arrival_time=next_weekday_at_830(),
    )

    duration_text_pt = work_directions_pt[0]["legs"][0]["duration"]["text"]
    distance_text_pt = work_directions_pt[0]["legs"][0]["distance"]["text"]
    duration_value_pt = work_directions_pt[0]["legs"][0]["duration"]["value"]
    distance_value_pt = work_directions_pt[0]["legs"][0]["distance"]["value"]

    work_directions_car = gmaps.directions(
        origin=(origin_lat, origin_lng),
        destination=workplace.value,
        mode="driving",
        arrival_time=next_weekday_at_830(),
    )

    duration_text_car = work_directions_car[0]["legs"][0]["duration"]["text"]
    distance_text_car = work_directions_car[0]["legs"][0]["distance"]["text"]
    duration_value_car = work_directions_car[0]["legs"][0]["duration"]["value"]
    distance_value_car = work_directions_car[0]["legs"][0]["distance"]["value"]

    time_diff_car_pt = abs(
        round(duration_value_car / 60) - round(duration_value_pt / 60)
    )

    if duration_value_car > duration_value_pt:
        work_duration_pt_stat_dir = "increase"
        work_duration_car_stat_dir = "decrease"
    elif duration_value_car < duration_value_pt:
        work_duration_pt_stat_dir = "decrease"
        work_duration_car_stat_dir = "increase"
    else:
        work_duration_pt_stat_dur = None
        work_duration_car_stat_dir = None
    return (
        duration_text_car,
        duration_text_pt,
        time_diff_car_pt,
        work_duration_car_stat_dir,
        work_duration_pt_stat_dir,
    )


@app.cell
def _(
    duration_text_car,
    duration_text_pt,
    mo,
    time_diff_car_pt,
    work_duration_car_stat_dir,
    work_duration_pt_stat_dir,
):
    work_duration_pt_stat = mo.stat(
        value=duration_text_pt,
        label="Public Transport Commute Time",
        caption=f"{time_diff_car_pt} mins compared to driving",
        direction=work_duration_pt_stat_dir,
    )

    work_duration_car_stat = mo.stat(
        value=duration_text_car,
        label="Driving Commute Time",
        caption=f"{time_diff_car_pt} mins compared to public transport",
        direction=work_duration_car_stat_dir,
    )

    mo.hstack([work_duration_pt_stat, work_duration_car_stat], justify="center")
    return


@app.cell
def _(
    folium,
    formatted_address,
    get_nearby,
    mo,
    origin_lat,
    origin_lng,
    plot_nearby,
):
    map = folium.Map(location=[origin_lat, origin_lng], zoom_start=15)
    folium.Marker(
        [origin_lat, origin_lng],
        tooltip=formatted_address,
        icon=folium.Icon(icon="home"),
    ).add_to(map)
    plot_nearby(
        map,
        get_nearby((origin_lat, origin_lng), "woolworths or coles or aldi"),
        icon=folium.Icon(
            icon="basket-shopping", prefix="fa", color="green", icon_color="white"
        ),
    )
    plot_nearby(
        map,
        get_nearby((origin_lat, origin_lng), "gym"),
        icon=folium.Icon(
            icon="dumbbell", prefix="fa", color="red", icon_color="white"
        ),
    )

    mo.Html(map._repr_html_())
    return


@app.cell
def _(folium, origin_lat, origin_lng):
    import geopandas as gpd

    sa1_map = folium.Map(location=[origin_lat, origin_lng], zoom_start=15)

    sa1_gdf = gpd.read_file("property_analyser/data/SA1_2021_AUST_SHP_GDA2020/SA1_2021_AUST_GDA2020.shp")
    sa1_gdf = sa1_gdf[sa1_gdf["STE_NAME21"] == "Western Australia"]
    # sa1_gdf = sa1_gdf[sa1_gdf["GCC_NAME21"] == "Greater Perth"]
    # sa1_gdf = sa1_gdf[sa1_gdf["SA4_NAME21"] == "Perth - Inner"]

    folium.GeoJson(sa1_gdf).add_to(sa1_map)

    # mo.Html(sa1_map._repr_html_())
    return (sa1_gdf,)


@app.cell
def _(sa1_gdf):
    sa1_gdf
    return


@app.cell
def _(origin_lat, origin_lng, sa1_gdf):
    from shapely.geometry import Point

    origin_point = Point(origin_lng, origin_lat)
    sa1_gdf[sa1_gdf.geometry.contains(origin_point)]
    return


@app.cell
def _(sa1_gdf):
    sa1_gdf.crs
    return


@app.cell
def _():
    import pandas as pd

    social_housing = pd.read_parquet("property_analyser/data/atlas_rent_social_housing.parquet")

    social_housing
    return (social_housing,)


@app.cell
def _(
    folium,
    formatted_address,
    mo,
    origin_lat,
    origin_lng,
    sa1_gdf,
    social_housing,
):
    social_housing_gdf = sa1_gdf.merge(social_housing, left_on="SA1_CODE21", right_on="SA1", how="inner")

    social_housing_map = folium.Map(location=[origin_lat, origin_lng], zoom_start=15)
    folium.Marker(
        [origin_lat, origin_lng],
        tooltip=formatted_address,
        icon=folium.Icon(icon="home"),
    ).add_to(social_housing_map)

    # folium.GeoJson(social_housing_gdf).add_to(social_housing_map)
    social_housing_gdf.explore(column="Percentage", cmap="bwr", vmin=0, vmax=0.1, m=social_housing_map)

    mo.Html(social_housing_map._repr_html_())
    return


if __name__ == "__main__":
    app.run()
