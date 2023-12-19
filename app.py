import streamlit as st
import geopandas as gpd
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium
from pathlib import Path
import janitor

st.set_page_config(layout="wide")

# Load data


@st.cache_data
def load_data():
    clean_data_path = "https://github.com/fedderw/baltimore-city-crash-analysis/blob/74adb465cced95c0708b4ffae74e6d987c482c35/data/clean/crash_data.geojson?raw=true"
    city_council_district_geojson_path = "https://github.com/fedderw/baltimore-city-crash-analysis/blob/74adb465cced95c0708b4ffae74e6d987c482c35/data/clean/city_council_districts.geojson?raw=true"
    neighborhoods_url = "https://services1.arcgis.com/UWYHeuuJISiGmgXx/arcgis/rest/services/Neighborhood/FeatureServer/0/query?outFields=*&where=1%3D1&f=geojson"

    gdf = gpd.read_file(clean_data_path)
    city_council_districts = gpd.read_file(
        city_council_district_geojson_path
    ).clean_names()
    neighborhoods = gpd.read_file(neighborhoods_url).clean_names()

    return gdf, city_council_districts, neighborhoods


# Streamlit app


def main():
    st.title("Crashes resulting in injury or death")

    # Sidebar options

    base_map = st.sidebar.selectbox(
        "Select Base Map",
        [
            "OpenStreetMap",
            "Stamen Terrain",
            "Stamen Toner",
            "Stamen Watercolor",
            "CartoDB positron",
            "CartoDB dark_matter",
        ],
    )
    show_districts = st.sidebar.checkbox("Show City Council Districts")
    show_neighborhoods = st.sidebar.checkbox("Show Neighborhoods")
    non_motorist_filter = st.sidebar.checkbox(
        "Show Only Non-Motorist Involved Crashes", value=True
    )

    # Load data

    gdf, city_council_districts, neighborhoods = load_data()

    # Apply non-motorist filter

    if non_motorist_filter:
        gdf = gdf[gdf["non_motorist_involved"] == True]
    # Create map

    m = folium.Map(
        location=[gdf.geometry.y.mean(), gdf.geometry.x.mean()],
        zoom_start=11,
        tiles=base_map,
    )

    # Heatmap

    heat_data = [[point.xy[1][0], point.xy[0][0]] for point in gdf.geometry]
    HeatMap(heat_data).add_to(m)

    # Districts layer

    if show_districts:
        folium.GeoJson(
            city_council_districts,
            style_function=lambda x: {
                "fillColor": "transparent",
                "color": "black",
                "weight": 2,
            },
        ).add_to(m)
    # Neighborhoods layer

    if show_neighborhoods:
        folium.GeoJson(
            neighborhoods,
            style_function=lambda x: {
                "fillColor": "transparent",
                "color": "red",
                "weight": 2,
            },
        ).add_to(m)
    # Display map

    st_folium(m, width=900, height=800)


if __name__ == "__main__":
    main()
