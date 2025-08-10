import marimo

__generated_with = "0.14.16"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    from dotenv import load_dotenv
    import googlemaps
    import os

    load_dotenv()
    return googlemaps, os


@app.cell
def _(googlemaps, os):
    gmaps = googlemaps.Client(key=os.getenv("GMAPS_API_KEY"))
    return (gmaps,)


@app.cell
def _(gmaps):
    geocode_result = gmaps.geocode("some property location")
    return (geocode_result,)


@app.cell
def _(geocode_result):
    location = geocode_result[0]["geometry"]["location"]
    origin_lat = location["lat"]
    origin_lng = location["lng"]
    return origin_lat, origin_lng


@app.cell
def _(gmaps, origin_lat, origin_lng):
    places_result = gmaps.places_nearby(
        location=(origin_lat, origin_lng),
        radius=5000,
        type="shopping_mall"
    )
    return (places_result,)


@app.cell
def _(places_result):
    for place in places_result["results"]:
        print(f"name: {place["name"]}")
        print(f"lat: {place['geometry']['location']['lat']}, lng: {place['geometry']['location']['lng']}\n")
    return


if __name__ == "__main__":
    app.run()
