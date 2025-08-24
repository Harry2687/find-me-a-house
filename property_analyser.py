import marimo

__generated_with = "0.15.0"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    from dotenv import load_dotenv
    import googlemaps
    import os
    import polars as pl
    import folium

    load_dotenv()

    gmaps = googlemaps.Client(key=os.getenv("GMAPS_API_KEY"))
    return folium, gmaps, mo, os, pl


@app.cell
def _(mo, os):
    # Define Marimo input objects
    address = mo.ui.text_area(value=os.getenv("MY_ADDRESS"), placeholder="Enter property address...")
    search_term = mo.ui.text(value="coles or woolworths or aldi")
    travel_mode = mo.ui.dropdown(options=["walking", "driving", "transit"], value="walking")
    return address, search_term, travel_mode


@app.cell
def _(address, mo, search_term, travel_mode):
    mo.md(
        f"""
    # Inputs
    Address: {address}\n
    Search: {search_term}\n
    Travel mode: {travel_mode}
    """
    )
    return


@app.cell
def _(address, gmaps):
    geocode_result = gmaps.geocode(address.value)
    return (geocode_result,)


@app.cell
def _(geocode_result):
    location = geocode_result[0]["geometry"]["location"]
    origin_lat = location["lat"]
    origin_lng = location["lng"]
    origin = (origin_lat, origin_lng)

    formatted_address = geocode_result[0]["formatted_address"]
    location_id = geocode_result[0]["place_id"]
    return formatted_address, origin, origin_lat, origin_lng


@app.cell
def _(formatted_address, mo):
    mo.md(f"""Address search result: {formatted_address}""")
    return


@app.cell
def _(gmaps, pl):
    def get_nearby(
        origin: tuple, search_term: str, travel_mode: str = "walking"
    ) -> pl.DataFrame:
        places_nearby_result = gmaps.places_nearby(
            location=origin, keyword=search_term, rank_by="distance"
        )

        places_nearby_ids = [
            "place_id:" + place["place_id"]
            for place in places_nearby_result["results"]
        ]

        distance_matrix_result = gmaps.distance_matrix(
            origins=origin, destinations=places_nearby_ids, mode=travel_mode
        )

        destinations = distance_matrix_result["destination_addresses"]
        distances = distance_matrix_result["rows"][0]["elements"]

        places_nearby_result_data = places_nearby_result["results"]

        places_nearby_df = pl.DataFrame(
            [
                {
                    "Id": result.get("place_id"),
                    "Name": result.get("name"),
                    "Address": result.get("vicinity"),
                    "Rating": result.get("rating"),
                    "Total Ratings": result.get("user_ratings_total"),
                }
                for result in places_nearby_result_data
            ]
        )

        distance_matrix_df = pl.DataFrame(
            {
                "Id": [id.replace("place_id:", "") for id in places_nearby_ids],
                "Destination": destinations,
                "Distance": [d["distance"]["text"] for d in distances],
                f"{travel_mode} Duration": [d["duration"]["text"] for d in distances],
            }
        )

        return places_nearby_df.join(distance_matrix_df, on="Id").select(
            "Name",
            "Address",
            "Rating",
            "Total Ratings",
            "Distance",
            f"{travel_mode} Duration",
        )
    return


@app.cell
def _(gmaps, origin, pl, search_term):
    def get_nearby_2(origin: tuple, search_term: str):
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

    get_nearby_2(origin=origin, search_term=search_term.value)
    return (get_nearby_2,)


@app.cell
def _(
    folium,
    formatted_address,
    get_nearby_2,
    mo,
    origin,
    origin_lat,
    origin_lng,
):
    poi = get_nearby_2(origin=origin, search_term="gym")

    map = folium.Map(location=[origin_lat, origin_lng], zoom_start=15)
    folium.Marker([origin_lat, origin_lng], tooltip=formatted_address, icon=folium.Icon(icon="home")).add_to(map)

    for row in poi.iter_rows(named=True):
        folium.Marker(
            [row["lat"], row["lng"]], 
            tooltip=row["Name"], 
            popup=f"Walking Duration: {row["Walking Duration"]}\nDriving Duration: {row["Driving Duration"]}"
        ).add_to(map)

    mo.Html(map._repr_html_())
    return


if __name__ == "__main__":
    app.run()
