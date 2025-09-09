import marimo

__generated_with = "0.15.2"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import requests
    from bs4 import BeautifulSoup
    import os
    import polars as pl
    return BeautifulSoup, os, pl, requests


@app.cell
def _(BeautifulSoup, requests):
    url = "https://atlas.id.com.au/"
    resp = requests.get(url)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    links = [a["href"] for a in soup.find_all("a", href=True)]
    atlas_links = [
        l
        for l in links
        if l.startswith("https://atlas.id.com.au/")
        and l != "https://atlas.id.com.au/wapl" # wapl is not aggregated at SA1 level
    ]
    return (atlas_links,)


@app.cell
def _(atlas_links, os, requests):
    for base_url in atlas_links:
        city_name = base_url.split("/")[-1]
        saved_file_path = f"property_analyser/data/atlas_rent_social_housing/rent_social_housing_{city_name}.csv"
        if not os.path.exists(saved_file_path):
            rent_social_housing_url = f"{base_url}/geo/data/10059/?Year=2021&DataType=1&SexKey=4&MapNo=10059&themtype=1&export=csv"
            rent_social_housing_resp = requests.get(rent_social_housing_url)
            rent_social_housing_resp.raise_for_status()

            with open(saved_file_path, "wb") as f:
                f.write(rent_social_housing_resp.content)

            print(f"Downloaded rent social housing dataset for {city_name}")
    return


@app.cell
def _(os, pl):
    csv_dir_path = "property_analyser/data/atlas_rent_social_housing"
    csv_pattern = os.path.join(csv_dir_path, "*.csv")
    rent_social_housing_agg_df = pl.read_csv(csv_pattern, skip_rows=1)
    rent_social_housing_agg_df = (
        rent_social_housing_agg_df.filter(pl.col("Number").is_not_null())
        .select("SA1", "Number", "Households")
        .with_columns(pl.col("Households").str.replace_all(",", "").cast(pl.Int64))
        .unique()
        .with_columns(
            (pl.col("Number") / pl.col("Households")).alias("Percentage")
        )
    )
    return (rent_social_housing_agg_df,)


@app.cell
def _(rent_social_housing_agg_df):
    rent_social_housing_agg_df.write_parquet("property_analyser/data/atlas_rent_social_housing.parquet")
    return


if __name__ == "__main__":
    app.run()
