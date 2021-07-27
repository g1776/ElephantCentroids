import streamlit as st
from OSMPythonTools.overpass import overpassQueryBuilder
from OSMPythonTools.overpass import Overpass
from shapely.geometry import Point
import pandas as pd
import folium
from geopandas import GeoDataFrame, read_file

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



def get_settlements(centroids, progress, size=1, n=10):
    # get settlements
    progress.text("getting human settlements")

    center_lat = centroids["location-lat"].median()
    center_long= centroids["location-long"].median()
    places = _get_nearby_settlements(center_lat, center_long, size=size)

    # get n closest settlements
    progress.text(f"calculating {n} closest human settlements")
    closest_places = _get_close_places(places, centroids, n=n)
    centroids_geo = centroids[["tag-local-identifier", "geometry"]]
    places_geo = places[["id", "name", "geometry"]]
    closest_geo = pd.merge(closest_places, centroids_geo, how="left", left_on="centroid_index", right_index=True)
    closest_geo = pd.merge(closest_geo, places_geo, left_on="place_id", right_on="id", suffixes=("_elephant", "_place"))
    closest_geo.drop("id", axis=1, inplace=True)

    return places, closest_geo


def pop_choropleth(zip, m):
    pop = read_file(zip, encoding='utf-8')
    pop.crs = "EPSG:4326"
    ranges = list(pop.RANGE.unique())
    colors = ['#556b2f', '#191970', '#ff4500', '#ffd700', '#00ff7f', '#00bfff', '#0000ff', '#ff1493']
    choropleth = folium.GeoJson(data=pop, name="Population density",
        show=False,
        style_function=lambda feature: {
            'fillColor': colors[ranges.index(feature['properties']["RANGE"])],
            'fillOpacity': 0.1
        }
    ).add_to(m)
    choropleth.add_child(folium.features.GeoJsonTooltip(
        fields=['RANGE'],
        aliases=['Population density per km^2'],
        style=('background-color: grey; color: white;'),
        localize=True))