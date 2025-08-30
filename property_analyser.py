import marimo

__generated_with = "0.15.2"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    from dotenv import load_dotenv
    import googlemaps
    import os
    import polars as pl
    import folium
    import datetime

    load_dotenv()

    gmaps = googlemaps.Client(key=os.getenv("GMAPS_API_KEY"))
    return datetime, folium, gmaps, mo, os, pl


@app.cell
def _(mo, os):
    # Define Marimo input objects
    address = mo.ui.text_area(value=os.getenv("MY_ADDRESS"), placeholder="Enter property address...")
    workplace = mo.ui.text_area(value=os.getenv("WORK"), placeholder="Enter work address...")
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
def _(gmaps, next_weekday_at_830, origin_lat, origin_lng, workplace):
    work_directions = gmaps.directions(origin=(origin_lat, origin_lng), destination=workplace.value, mode="transit", arrival_time=next_weekday_at_830())
    duration = work_directions[0]["legs"][0]["duration"]["text"]
    distance = work_directions[0]["legs"][0]["distance"]["text"]
    return distance, duration


@app.cell
def _(distance, duration, formatted_address, mo):
    mo.md(
        f"""
    Address search result: {formatted_address}\n
    It will take {duration} to travel {distance} to work.
    """
    )
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
            color="green", icon="basket-shopping", prefix="fa", icon_color="white"
        ),
    )
    plot_nearby(
        map,
        get_nearby((origin_lat, origin_lng), "gym"),
        icon=folium.Icon(
            color="red", icon="dumbbell", prefix="fa", icon_color="white"
        ),
    )

    mo.Html(map._repr_html_())
    return


@app.cell
def _(datetime):
    def next_weekday_at_830():
        date = datetime.date.today()

        while date.weekday() > 4:
            date += datetime.timedelta(days=1)
    
        return datetime.datetime.combine(date, datetime.time(8, 30))
    return (next_weekday_at_830,)


@app.cell
def _(gmaps, pl):
    def get_nearby(origin: tuple, search_term: str):
        places_nearby_result = gmaps.places_nearby(
            location=origin, keyword=search_term, rank_by="distance"
        )

        places_nearby_ids = [
            "place_id:" + place["place_id"]
            for place in places_nearby_result["results"]
        ]

        places_nearby_result_data = places_nearby_result["results"]

        places_nearby_df = pl.DataFrame(
            [
                {
                    "Id": result.get("place_id"),
                    "Name": result.get("name"),
                    "Rating": result.get("rating"),
                    "Total Ratings": result.get("user_ratings_total"),
                    "lat": result["geometry"]["location"]["lat"],
                    "lng": result["geometry"]["location"]["lng"],
                }
                for result in places_nearby_result_data
            ]
        )

        distance_matrix_walking = gmaps.distance_matrix(
            origins=origin, destinations=places_nearby_ids, mode="walking"
        )

        distances_walking = distance_matrix_walking["rows"][0]["elements"]

        distance_matrix_driving = gmaps.distance_matrix(
            origins=origin, destinations=places_nearby_ids, mode="driving"
        )

        distances_driving = distance_matrix_driving["rows"][0]["elements"]

        distance_matrix_df = pl.DataFrame(
            {
                "Id": [id.replace("place_id:", "") for id in places_nearby_ids],
                "Walking Distance": [d["distance"]["text"] for d in distances_walking],
                "Walking Duration": [d["duration"]["text"] for d in distances_walking],
                "Driving Distance": [d["distance"]["text"] for d in distances_driving],
                "Driving Duration": [d["duration"]["text"] for d in distances_driving],
            }
        )

        output_df = places_nearby_df.join(distance_matrix_df, on="Id").select(
            "Name",
            "lat",
            "lng",
            "Rating",
            "Total Ratings",
            "Walking Distance",
            "Walking Duration",
            "Driving Distance",
            "Driving Duration"
        )

        return output_df
    return (get_nearby,)


@app.cell
def _(folium, pl):
    def plot_nearby(map: folium.Map, nearby_points: pl.DataFrame, icon: folium.Icon):
        for row in nearby_points.iter_rows(named=True):
            folium.Marker(
                [row["lat"], row["lng"]], 
                tooltip=row["Name"], 
                popup=f"Walking Duration: {row["Walking Duration"]}\nDriving Duration: {row["Driving Duration"]}",
                icon=icon
            ).add_to(map)

        return None
    return (plot_nearby,)


if __name__ == "__main__":
    app.run()
