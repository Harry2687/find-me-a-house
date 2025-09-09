import marimo

__generated_with = "0.15.2"
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


if __name__ == "__main__":
    app.run()
