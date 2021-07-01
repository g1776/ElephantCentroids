import streamlit as st
from OSMPythonTools.overpass import overpassQueryBuilder
from OSMPythonTools.overpass import Overpass
from shapely.geometry import Point
import pandas as pd
from geopandas import GeoDataFrame

def _get_nearby_settlements(lat, long, size=1):
    overpass = Overpass()

    ## bbox to get places in 
    bbox=[lat-size, long-size, lat+size,long+size]

    query = overpassQueryBuilder(
        bbox=bbox,
        elementType='node', 
        selector='place~"city|town|village|hamlet"',
        out='body'
    )

    res = overpass.query(query, timeout=50)

    places = pd.DataFrame(res.toJSON()['elements'])
    places = places.drop('tags', axis=1).join(pd.DataFrame(places.tags.values.tolist()))
    places["geometry"] = places.apply(lambda row: Point([row["lon"], row["lat"]]), axis=1)
    places = GeoDataFrame(places, geometry="geometry")

    return places


def _get_close_places(places, centroids, n=10):
    distances = []

    for i, place in places.iterrows():
        for j, elephant in centroids.iterrows():
            distances.append({
                "place_id": place.loc["id"],
                "centroid_index": j,
                "distance": place.loc["geometry"].distance(elephant.loc["geometry"])
            })
    distances = pd.DataFrame(distances)
    closest = distances.sort_values("distance").head(n)

    return closest



def get_settlements(centroids, progress):
    # get settlements
    progress.text("getting human settlements")

    center_lat = centroids["location-lat"].median()
    center_long= centroids["location-long"].median()
    places = _get_nearby_settlements(center_lat, center_long)

    # get n closest settlements
    n = 10
    progress.text(f"calculating {n} closest human settlements")
    closest_places = _get_close_places(places, centroids, n=n)
    centroids_geo = centroids[["tag-local-identifier", "geometry"]]
    places_geo = places[["id", "name", "geometry"]]
    closest_geo = pd.merge(closest_places, centroids_geo, how="left", left_on="centroid_index", right_index=True)
    closest_geo = pd.merge(closest_geo, places_geo, left_on="place_id", right_on="id", suffixes=("_elephant", "_place"))
    closest_geo.drop("id", axis=1, inplace=True)

    return places, closest_geo