import streamlit as st
import pandas as pd
import json
import folium
# from ipyleaflet import Map, basemaps, GeoJSON, Icon, Marker, MarkerCluster, FullScreenControl, Polyline
# from ipywidgets import HTML


def plot_centroids(m, centroids):

    id = centroids["tag-local-identifier"].iloc[0]


    # plot centroids
    cluster = folium.plugins.MarkerCluster().add_to(m)

    def add_marker(centroid):
        text = f'<b>{centroid["tag-local-identifier"]}</b><br/>{centroid["feature space"]}'
        elephant_icon = folium.features.CustomIcon(icon_image='./img/elephant.png', icon_size=(30,30))
        marker = folium.Marker([centroid["location-lat"], centroid["location-long"]],
                        popup=text,
                        tooltip=text,
                        icon=elephant_icon
        ).add_to(cluster)

        return marker

    markers = centroids.apply(add_marker, axis=1)

    return markers


def plot_places(m, places, lines, progress):
    # plot places
    for i, row in places.iterrows():
        text = f'<b>{row.loc["name"]}</b>'
        house_icon = folium.features.CustomIcon(icon_image='./img/house.png', icon_size=(35,35))
        folium.Marker(
            [row.lat, row.lon], 
            popup=text, 
            tooltip=text, 
            icon=house_icon
        ).add_to(m)


    # plot closest_geo
    progress.text('Plotting "closest" lines')
    for i, row in lines.iterrows():
        points = [list(list(row.geometry_elephant.coords)[0])[::-1], # lat long order is wrong
                list(list(row.geometry_place.coords)[0])[::-1]]
        folium.PolyLine(
            points,
            color="green"
        ).add_to(m)