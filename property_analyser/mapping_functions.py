import marimo

__generated_with = "0.15.3"
app = marimo.App(width="medium")

with app.setup:
    # Initialization code that runs before all other cells
    import marimo as mo
    from dotenv import load_dotenv
    import googlemaps
    import os
    import polars as pl
    import folium
    import datetime

    load_dotenv()

    gmaps = googlemaps.Client(key=os.getenv("GMAPS_API_KEY"))


@app.function
def next_weekday_at_830():
    date = datetime.date.today()

    while date.weekday() > 4:
        date += datetime.timedelta(days=1)

    return datetime.datetime.combine(date, datetime.time(8, 30))


@app.function
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
            "Walking Distance": [
                d["distance"]["text"] for d in distances_walking
            ],
            "Walking Duration": [
                d["duration"]["text"] for d in distances_walking
            ],
            "Driving Distance": [
                d["distance"]["text"] for d in distances_driving
            ],
            "Driving Duration": [
                d["duration"]["text"] for d in distances_driving
            ],
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
        "Driving Duration",
    )

    return output_df


@app.function
def plot_nearby(
    map: folium.Map, nearby_points: pl.DataFrame, icon: folium.Icon
):
    for row in nearby_points.iter_rows(named=True):
        folium.Marker(
            [row["lat"], row["lng"]],
            tooltip=row["Name"],
            popup=f"Walking Duration: {row['Walking Duration']}\nDriving Duration: {row['Driving Duration']}",
            icon=icon,
        ).add_to(map)

    return None


@app.function
def get_commute_stats(origin: tuple, destination: tuple, arrival_time: datetime.datetime):
    work_directions_pt = gmaps.directions(
        origin=origin,
        destination=destination,
        mode="transit",
        arrival_time=arrival_time,
    )
    
    duration_text_pt = work_directions_pt[0]["legs"][0]["duration"]["text"]
    distance_text_pt = work_directions_pt[0]["legs"][0]["distance"]["text"]
    duration_value_pt = work_directions_pt[0]["legs"][0]["duration"]["value"]
    distance_value_pt = work_directions_pt[0]["legs"][0]["distance"]["value"]
    
    work_directions_car = gmaps.directions(
        origin=origin,
        destination=destination,
        mode="driving",
        arrival_time=arrival_time,
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

    return [work_duration_pt_stat, work_duration_car_stat]


if __name__ == "__main__":
    app.run()
