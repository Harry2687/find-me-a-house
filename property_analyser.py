import marimo

__generated_with = "0.14.17"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    from dotenv import load_dotenv
    import googlemaps
    import os
    import polars as pl

    load_dotenv()

    gmaps = googlemaps.Client(key=os.getenv("GMAPS_API_KEY"))
    return gmaps, mo, os, pl


@app.cell
def _(mo, os):
    # Define Marimo input objects
    address = mo.ui.text(value=os.getenv("MY_ADDRESS"))
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
    return formatted_address, origin


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
                "Walking Duration": [d["duration"]["text"] for d in distances],
            }
        )

        return places_nearby_df.join(distance_matrix_df, on="Id").select(
            "Name",
            "Address",
            "Rating",
            "Total Ratings",
            "Distance",
            "Walking Duration",
        )
    return (get_nearby,)


@app.cell
def _(get_nearby, origin, search_term, travel_mode):
    get_nearby(origin=origin, search_term=search_term.value, travel_mode=travel_mode.value)
    return


if __name__ == "__main__":
    app.run()
