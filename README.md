
# Baltimore City Crash Analysis

## Overview
This Python application visualizes crashes involving non-motorists resulting in injury or death in Baltimore City. It employs Streamlit for web application framework, DuckDB for spatial data processing, and Folium for interactive mapping.

## Installation
To run this application, you need to install the following Python packages:
- streamlit
- geopandas
- folium
- streamlit_folium
- janitor
- duckdb
- pandas

You can install these packages via pip:
```
pip install -r requirements.txt
```

## Usage
After installing the necessary packages, run the Streamlit application:
```
streamlit run your_script_name.py
```

## Features
- Spatial analysis using DuckDB.
- Interactive mapping with Folium in Streamlit.
- Filtering data based on date range and various map layers including city council districts, neighborhoods, and camera locations.
- Customizable heatmap settings for better visualization.

## Data Sources
- Crash data from Maryland State Police Crash Reporting Dashboard.
- City council district and neighborhood boundaries from Open Baltimore.
- Red light and speed camera locations from ArcGIS servers.

## Application Structure
1. **Data Loading**: Load geospatial data using GeoPandas and process it using DuckDB for spatial queries.
2. **Streamlit Interface**: Utilize Streamlit to create an interactive web application.
3. **Mapping**: Implement Folium to generate interactive maps with heatmaps and various layers.
4. **Session State Management**: Manage UI state for interactivity and user inputs.

## Code Snippets
### Data Loading Function
```python
@st.cache_data
def load_data():
    # Code for data loading and processing
```

### Heatmap Configuration
```python
heatmap_defaults = {
    "radius": 8,
    "blur": 6,
    "min_opacity": 0.3,
    "gradient": {0.2: "blue", 0.4: "lime", 0.6: "yellow", 1: "red"},
}
```
The heatmap defaults are used to configure the heatmap layer in Folium, but this app also provides in-app customization of the heatmap settings.

It can be a little tricky to find a good set of heatmap settings for a given dataset. 

Some settings look better at the city-wide zoom-level, whereas others look better at the neighborhood-level. 

The defaults above are the result of some trial and error to find a happy medium that highlights specific problem *intersections*. 

Setting a higher radius and blur makes the heatmap look better when highlighting general *areas* of high crash density.


## Contributions
Feel free to contribute to this project by submitting issues or pull requests.

## License
This project is licensed under the MIT License.

## Links
- [Application GitHub Repository](https://github.com/fedderw/baltimore-crash-heat-map)
- [Original Data Source](https://mdsp.maryland.gov/Pages/Dashboards/CrashDataDownload.aspx)

