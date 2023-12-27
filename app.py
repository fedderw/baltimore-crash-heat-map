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


defaults = {
    "radius": 8,
    "blur": 6,
    "min_opacity": 0.3,
    "gradient": {0.2: "blue", 0.4: "lime", 0.6: "yellow", 1: "red"},
}


# Reset defaults function
def reset_defaults():
    st.session_state.radius = defaults["radius"]
    st.session_state.blur = defaults["blur"]
    st.session_state.min_opacity = defaults["min_opacity"]


def main():
    st.title("Crashes resulting in injury or death")
    st.write("Data from 1/1/2018 to 12/11/2023")

    # Initialize session state variables
    if "radius" not in st.session_state:
        st.session_state.radius = defaults["radius"]
    if "blur" not in st.session_state:
        st.session_state.blur = defaults["blur"]
    if "min_opacity" not in st.session_state:
        st.session_state.min_opacity = defaults["min_opacity"]

    # Sidebar options
    base_map = st.sidebar.selectbox(
        "Select Base Map",
        [
            "CartoDB positron",
            "CartoDB dark_matter",
            "OpenStreetMap",
        ],
    )
    show_districts = st.sidebar.checkbox("Show City Council Districts")
    show_neighborhoods = st.sidebar.checkbox("Show Neighborhoods")
    non_motorist_filter = st.sidebar.checkbox(
        "Show Only Non-Motorist Involved Crashes", value=True
    )

    # Create a slider for the radius of the heatmap
    st.sidebar.markdown("## Heatmap Options")
    st.session_state.radius = st.sidebar.slider(
        "Radius (in pixels)", min_value=1, max_value=100, value=st.session_state.radius
    )
    st.session_state.blur = st.sidebar.slider(
        "Blur (in pixels)", min_value=1, max_value=100, value=st.session_state.blur
    )
    st.session_state.min_opacity = st.sidebar.slider(
        "Min Opacity", min_value=0.0, max_value=1.0, value=st.session_state.min_opacity
    )

    # Option to reset to default values
    if st.sidebar.button("Reset to Default Values"):
        reset_defaults()

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
    HeatMap(
        heat_data,
        radius=st.session_state.radius,
        blur=st.session_state.blur,
        min_opacity=st.session_state.min_opacity,
        gradient=defaults["gradient"],
    ).add_to(m)

    print(f"Radius: {st.session_state.radius}")
    print(f"Blur: {st.session_state.blur}")
    print(f"Min Opacity: {st.session_state.min_opacity}")
    print(f"Gradient: {defaults['gradient']}")

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
