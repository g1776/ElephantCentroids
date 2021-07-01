import streamlit as st
import pandas as pd
from streamlit_folium import folium_static
from geopandas import read_file
import folium

from foliumMap import plot_centroids, plot_places
from utils import get_settlements

# setup
st.set_page_config(layout="wide") 


# header
st.markdown("# DBSCAN Centroids Map Tool")
st.markdown("## Gregory Glatzer")


# inputs
dataset = st.selectbox(
    'Choose which dataset to view',
    ("Etosha", 'Kruger', "Forest Elephants"),
)
if dataset == "Kruger":
    centroids_fp = './data/kruger_centroids.json'
elif dataset == "Etosha":
    centroids_fp = './data/etosha_centroids.json'
elif dataset == "Forest Elephants":
    centroids_fp = './data/forest_centroids.json'
    
fuzzy = st.checkbox("Use fuzzy matches", value=True)



# read in data
centroids = read_file(centroids_fp)
centroids = centroids[centroids.fuzzy == fuzzy]
centroids.columns = ["location-long", "location-lat", "stationTemp", 
    "cluster", "feature space", "tag-local-identifier", "fuzzy", "geometry"]

# layout placeholders
col1, col2, col3 = st.beta_columns((3,1, 1))
with col3:
    st.markdown("## Toggle elephants")
    checkboxes = []
    for id in centroids['tag-local-identifier'].unique():
        checkboxes.append([id, st.checkbox(id, value=True)])

# process
with col1:
    loading = st.markdown("### loading...")
    progress = st.empty()
    gif_runner = st.image('./img/elephant.gif')


# create map
center_lat = centroids["location-lat"].median()
center_long= centroids["location-long"].median()
center = [center_lat, center_long]
m = folium.Map(location=center, 
                zoom_start=8,
                zoom_control=True,
                scrollWheelZoom=True,
                dragging=True)
fs = folium.plugins.Fullscreen().add_to(m)
folium.TileLayer(
    tiles = 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    attr = 'Esri',
    name = 'Esri Satellite',
    overlay = False,
    control = True
).add_to(m)


# add places and centroids
progress.text("plotting elephant centroids")
places, lines = get_settlements(centroids, progress)
plot_places(m, places, lines, progress)
for id_checkbox in checkboxes:
    if id_checkbox[1]:
        id = id_checkbox[0]
        group = centroids[centroids["tag-local-identifier"] == id]
        progress.text(f"Plotting marker for {id}")
        markers = plot_centroids(m, group)

# content
progress.text("Rendering map")
with col1:
    folium_static(m)


# cleanup
gif_runner.empty()
loading.text('')
progress.text('')


