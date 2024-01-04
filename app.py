import streamlit as st
import geopandas as gpd
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium
from pathlib import Path
import janitor
import duckdb
import pandas as pd
import datetime

st.set_page_config(layout="wide")


# Load data
@st.cache_data
def load_data():
    counties_path = "data/external/maryland_county_boundaries.geojson"
    reports_path = "data/raw/CrashMap_REPORT_data.csv"
    nonmotorists_path = "data/raw/CrashMap_NONMOTORIST_data.csv"
    clean_data_path = "https://github.com/fedderw/baltimore-city-crash-analysis/blob/74adb465cced95c0708b4ffae74e6d987c482c35/data/clean/crash_data.geojson?raw=true"
    city_council_district_geojson_path = "https://github.com/fedderw/baltimore-city-crash-analysis/blob/74adb465cced95c0708b4ffae74e6d987c482c35/data/clean/city_council_districts.geojson?raw=true"
    neighborhoods_url = "https://services1.arcgis.com/UWYHeuuJISiGmgXx/arcgis/rest/services/Neighborhood/FeatureServer/0/query?outFields=*&where=1%3D1&f=geojson"
    red_light_cameras_url = "https://services3.arcgis.com/ZTvQ9NuONePFYofE/arcgis/rest/services/Baltimore_ATVES_Red_Light_Camera/FeatureServer/1/query?outFields=*&where=1%3D1&f=geojson"
    speed_cameras_url = "https://services3.arcgis.com/ZTvQ9NuONePFYofE/arcgis/rest/services/Baltimore_ATVES_Speed_Cameras/FeatureServer/0/query?outFields=*&where=1%3D1&f=geojson"

    # Start duckdb process
    duckdb.sql("INSTALL spatial")
    duckdb.sql("LOAD spatial")
    duckdb.sql(
        f"""
        CREATE 
        OR REPLACE TABLE counties AS 
        SELECT 
          county, 
          geom 
        FROM 
          ST_READ('{counties_path}')
        """
    )
    # Write a query to create a table of reports where the Latitute and Longitude are converted to a geometry column
    duckdb.sql(
        f"""
        CREATE 
        OR REPLACE TABLE reports AS 
        SELECT 
        *, 
        ST_POINT(Longitude, Latitude) AS geom 
        FROM 
        '{reports_path}'
        """
    )
    # Create a table of nonmotorists
    duckdb.sql(
        f"""
        CREATE 
        OR REPLACE TABLE nonmotorists AS 
        SELECT 
        * 
        FROM 
        '{nonmotorists_path}'
    """
    )
    nonmotorist_crashes = duckdb.sql(
        """
        SELECT 
            reports.ReportNumber, 
            reports.geom AS geometry, 
            ST_AsWKB(reports.geom) AS wkb,
            counties.county,
            ST_X(reports.geom) AS longitude,
            ST_Y(reports.geom) AS latitude,
            reports.Crashdate AS crash_date,
        FROM reports
        JOIN counties
        ON ST_WITHIN(reports.geom, counties.geom)
        WHERE counties.county = 'Baltimore City'
        AND reports.ReportNumber IN (
            SELECT ReportNumber
            FROM nonmotorists
            )
        """
    ).df()
    gdf = gpd.GeoDataFrame(
        nonmotorist_crashes,
        geometry=gpd.points_from_xy(
            nonmotorist_crashes.longitude, nonmotorist_crashes.latitude
        ),
    )
    city_council_districts = gpd.read_file(
        city_council_district_geojson_path
    ).clean_names()
    neighborhoods = gpd.read_file(neighborhoods_url).clean_names()
    red_light_cameras = gpd.read_file(red_light_cameras_url).clean_names()
    speed_cameras = gpd.read_file(speed_cameras_url).clean_names()

    return gdf, city_council_districts, neighborhoods, red_light_cameras, speed_cameras


heatmap_defaults = {
    "radius": 8,
    "blur": 6,
    "min_opacity": 0.3,
    "gradient": {0.2: "blue", 0.4: "lime", 0.6: "yellow", 1: "red"},
}


# Reset defaults function
def reset_defaults():
    st.session_state.radius = heatmap_defaults["radius"]
    st.session_state.blur = heatmap_defaults["blur"]
    st.session_state.min_opacity = heatmap_defaults["min_opacity"]


def main():
    st.title("Crashes involving non-motorists resulting in injury or death")

    # Load data
    (
        gdf,
        city_council_districts,
        neighborhoods,
        red_light_cameras,
        speed_cameras,
    ) = load_data()

    # Initialize session state variables
    if "radius" not in st.session_state:
        st.session_state.radius = heatmap_defaults["radius"]
    if "blur" not in st.session_state:
        st.session_state.blur = heatmap_defaults["blur"]
    if "min_opacity" not in st.session_state:
        st.session_state.min_opacity = heatmap_defaults["min_opacity"]
    if "zoom" not in st.session_state:
        st.session_state.zoom = 12
    if "center" not in st.session_state:
        st.session_state.center = [gdf.geometry.y.mean(), gdf.geometry.x.mean()]

    # Sidebar options
    base_map = st.sidebar.selectbox(
        "Select Base Map",
        [
            "CartoDB positron",
            "CartoDB dark_matter",
            "OpenStreetMap",
        ],
    )
    show_districts = st.sidebar.checkbox("Show city council district boundaries")
    show_neighborhoods = st.sidebar.checkbox("Show neighborhood boundaries")
    show_red_light_cameras = st.sidebar.checkbox("Show red light cameras")
    show_speed_cameras = st.sidebar.checkbox("Show speed cameras")

    start_date_input = st.sidebar.date_input("Start Date", gdf["crash_date"].min())
    # print(start_date_input)
    end_date_input = st.sidebar.date_input("End Date", gdf["crash_date"].max())
    if start_date_input > end_date_input:
        st.sidebar.error("End date must fall after start date.")
    else:
        gdf = gdf[
            gdf["crash_date"].between(
                datetime.datetime.combine(start_date_input, datetime.time.min),
                datetime.datetime.combine(end_date_input, datetime.time.max),
            )
        ]

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

    # Create map
    m = folium.Map(
        location=[39.2904, -76.6122],
        zoom_start=12,
        tiles=base_map,
    )

    # Heatmap
    heat_data = [[point.xy[1][0], point.xy[0][0]] for point in gdf.geometry]
    HeatMap(
        heat_data,
        radius=st.session_state.radius,
        blur=st.session_state.blur,
        min_opacity=st.session_state.min_opacity,
        gradient=heatmap_defaults["gradient"],
    ).add_to(m)

    # print(f"Radius: {st.session_state.radius}")
    # print(f"Blur: {st.session_state.blur}")
    # print(f"Min Opacity: {st.session_state.min_opacity}")
    # print(f"Gradient: {heatmap_defaults['gradient']}")

    

    # if show_red_light_cameras:
    #     for _, camera in red_light_cameras.iterrows():
    #         folium.Marker(
    #             location=[camera.geometry.y, camera.geometry.x],
    #             icon=folium.Icon(color="red", icon="camera"),
    #             tooltip="Red Light Camera",
    #         ).add_to(m)

    # if show_speed_cameras:
    #     for _, camera in speed_cameras.iterrows():
    #         folium.Marker(
    #             location=[camera.geometry.y, camera.geometry.x],
    #             icon=folium.Icon(color="blue", icon="camera"),
    #             tooltip="Speed Camera",
    #         ).add_to(m)
    # Districts layer
    city_council_districts_folium= folium.GeoJson(
            city_council_districts,
            style_function=lambda x: {
                "fillColor": "transparent",
                "color": "black",
                "weight": 2,
            },
        )

    # Neighborhoods layer
    neighborhoods_folium = folium.GeoJson(
            neighborhoods,
            style_function=lambda x: {
                "fillColor": "transparent",
                "color": "red",
                "weight": 2,
            },
        )
    
    city_council_districts_feature_group = folium.FeatureGroup(name='City Council Districts')
    city_council_districts_feature_group.add_child(city_council_districts_folium)
    
    neighborhoods_feature_group = folium.FeatureGroup(name='Neighborhoods')
    neighborhoods_feature_group.add_child(neighborhoods_folium)
    
    
    
    # Now, create a list of the feature groups we want to add to the map from the checkboxes
    fg_list = []
    
    if show_districts:
        fg_list.append(city_council_districts_feature_group)
        
    if show_neighborhoods:
        fg_list.append(neighborhoods_feature_group)
    

    if show_red_light_cameras:
        for _, camera in red_light_cameras.iterrows():
            folium.Marker(
                location=[camera.geometry.y, camera.geometry.x],
                icon=folium.Icon(color="red", icon="camera"),
                tooltip="Red Light Camera",
            ).add_to(m)

    if show_speed_cameras:
        for _, camera in speed_cameras.iterrows():
            folium.Marker(
                location=[camera.geometry.y, camera.geometry.x],
                icon=folium.Icon(color="blue", icon="camera"),
                tooltip="Speed Camera",
            ).add_to(m)

    # Display map
    st_data = st_folium(
        m,
        center=st.session_state["center"],
        zoom=st.session_state["zoom"],
        feature_group_to_add=fg_list,
        width=900,
        height=800,
    )
    # print(st_data['bounds'])
    # print(st_data["zoom"])
    # print(st.session_state["zoom"])
    # print(st_data["center"])
    # zoom = st_data["zoom"]

    # center = [st_data["center"]['lat'], st_data["center"]['lng']]

    readme_raw_url = "https://raw.githubusercontent.com/fedderw/baltimore-city-crash-analysis/74adb465cced95c0708b4ffae74e6d987c482c35/README.md"
    readme_url = "https://github.com/fedderw/baltimore-city-crash-analysis/blob/5111a0363e7d955a4a94a1b58f0703117635d54b/README.md"
    data_github_url = "https://github.com/fedderw/baltimore-city-crash-analysis"
    app_github_url = "https://github.com/fedderw/baltimore-crash-heat-map"
    crash_data_download_tool_url = "https://mdsp.maryland.gov/Pages/Dashboards/CrashDataDownload.aspx"

    st.markdown(f"## About")
    st.write(
        f"Data for this app was downloaded from the [Maryland State Police Crash Reporting Dashboard]({crash_data_download_tool_url}). Data was downloaded for Baltimore City and filtered to include only crashes involving non-motorists resulting in injury or death. The data was then converted to a GeoJSON file and loaded into a [DuckDB](https://duckdb.org/) database. The app uses [Streamlit](https://streamlit.io/) and [Folium](https://python-visualization.github.io/folium/) to display the data on a map."
    )
    st.write(
        f"See the app's [GitHub repository]({app_github_url}) for the app's source code."
    )


if __name__ == "__main__":
    main()
