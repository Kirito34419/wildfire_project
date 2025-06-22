import streamlit as st
import ee
import folium
from streamlit_folium import st_folium
import datetime
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import requests
import joblib
import os
import pandas as pd
import numpy as np
from math import radians, cos, sin, asin, atan2, degrees
import logging
from streamlit_extras.stylable_container import stylable_container
from streamlit_extras.grid import grid
from streamlit_extras.switch_page_button import switch_page
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO)

MODEL_PATH = os.path.join("models", "wildfire_rf_model.pkl")
model = joblib.load(MODEL_PATH)

st.set_page_config(layout="wide")

st.markdown("""
<style>
    .block-container {
        padding-top: 1rem;
        padding-bottom: 2rem;
    }
    .stRadio > div {
        display: flex;
        justify-content: center;
    }
    .stSelectbox > div {
        font-weight: bold;
    }
    .weather-metric {
        font-size: 0.85rem !important;
        line-height: 1.2;
    }
</style>
""", unsafe_allow_html=True)

st.title("🔥 Global Wildfire Risk & Real-Time Fire Alert System")

try:
    ee.Initialize(project='wildfiredetector')
except Exception as e:
    st.error(f"Earth Engine initialization failed: {e}")
    st.stop()

OPENWEATHER_API_KEY = "ad65aa96b1ba6f7c9a66eb1e0ccdf104"

# Map UI controls (floating row)
col1, col2, col3 = st.columns([1, 1, 2])
with col1:
    is_dark_mode = st.toggle("🌗 Dark Mode", value=False, key="dark_mode")
with col2:
    if st.button("🔁 Refresh Weather"):
        st.rerun()
with col3:
    if st.button("🔄 Refresh Map"):
        st.rerun()

def get_weather(lat, lon):
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric"
        response = requests.get(url)
        data = response.json()
        deg = data["wind"]["deg"]
        dirs = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
        compass_dir = dirs[int((deg + 22.5) % 360 // 45)]
        return {
            "wind_speed": data["wind"]["speed"],
            "wind_deg": deg,
            "wind_dir": compass_dir,
            "temperature": data["main"]["temp"],
            "humidity": data["main"]["humidity"]
        }
    except:
        return None

def compute_endpoint(lat, lon, bearing_deg, distance_km=20):
    R = 6371.0
    bearing = radians(bearing_deg)
    lat1 = radians(lat)
    lon1 = radians(lon)
    lat2 = asin(sin(lat1) * cos(distance_km / R) + cos(lat1) * sin(distance_km / R) * cos(bearing))
    lon2 = lon1 + atan2(sin(bearing) * sin(distance_km / R) * cos(lat1), cos(distance_km / R) - sin(lat1) * sin(lat2))
    return degrees(lat2), degrees(lon2)

def get_sector_points(center, direction_deg, radius_km=20, angle_width=60, num_points=10):
    points = [[center[0], center[1]]]
    start_angle = direction_deg - angle_width / 2
    step = angle_width / num_points
    for i in range(num_points + 1):
        angle = radians(start_angle + i * step)
        dlat = radius_km * cos(angle) / 6371.0
        dlon = radius_km * sin(angle) / (6371.0 * cos(radians(center[0])))
        lat = center[0] + degrees(dlat)
        lon = center[1] + degrees(dlon)
        points.append([lat, lon])
    return points

# Sidebar Inputs
with st.sidebar:
    st.header("🌍 Location & Filters")
    location = st.text_input("📍 Enter a location", "California")

    if "region_radius_km" not in st.session_state:
        st.session_state.region_radius_km = 50

    def update_radius_slider():
        st.session_state.region_radius_slider = st.session_state.region_radius_km

    def update_radius_number():
        st.session_state.region_radius_km = st.session_state.region_radius_slider

    st.number_input(
        "🧭 Region radius (km)",
        min_value=50,
        max_value=500,
        step=10,
        key="region_radius_km",
        on_change=update_radius_slider,
    )

    st.slider(
        "Adjust radius:",
        50,
        500,
        step=10,
        key="region_radius_slider",
        on_change=update_radius_number,
    )

    days_option = st.radio("🕒 Fire Alert Timeframe:", ["Only Today (Real-Time)", "Past 1 Day", "Past 3 Days", "Past Week"], index=0)

# Days back logic
if days_option == "Only Today (Real-Time)":
    days_back = 1
elif days_option == "Past 1 Day":
    days_back = 2
elif days_option == "Past 3 Days":
    days_back = 4
else:
    days_back = 8

geolocator = Nominatim(user_agent="wildfire_app", timeout=10)
try:
    loc = geolocator.geocode(location)
except (GeocoderTimedOut, GeocoderUnavailable):
    st.error("Geocoding failed. Try again later.")
    st.stop()
if not loc:
    st.error("Invalid location")
    st.stop()

lat, lon = loc.latitude, loc.longitude
region_radius_km = st.session_state.region_radius_km
region = ee.Geometry.Point([lon, lat]).buffer(region_radius_km * 1000).bounds()

# Dates
now = datetime.now(timezone.utc).date()
start_date = ee.Date.fromYMD(now.year, now.month, 1).advance(-3, 'month')
end_date = ee.Date.fromYMD(now.year, now.month, now.day)
firms_start = ee.Date.fromYMD(now.year, now.month, now.day).advance(-days_back, 'day')

# Earth Engine Data
burned = ee.ImageCollection("MODIS/061/MCD64A1").filterDate(start_date, end_date).filterBounds(region).select('BurnDate')
ndvi = ee.ImageCollection("MODIS/061/MOD13Q1").filterDate(start_date.advance(-1, 'month'), end_date).select('NDVI')

burned_img = burned.mosaic().clip(region)
ndvi_img = ndvi.median().clip(region)
low_ndvi = ndvi_img.lt(2000)
fire_detected = burned_img.gt(0).selfMask()
wildfire_risk = fire_detected.And(low_ndvi).selfMask()

viirs_raw = ee.ImageCollection("NASA/LANCE/NOAA20_VIIRS/C2") \
    .filterDate(firms_start, end_date) \
    .filterBounds(region)

viirs_count = viirs_raw.size().getInfo()
if viirs_count > 0:
    viirs = viirs_raw.select(["Bright_ti4", "Bright_ti5", "frp"])
    viirs_mean = viirs.mean().clip(region)
else:
    viirs = None
    viirs_mean = ee.Image().clip(region)

reverse = RateLimiter(geolocator.reverse, min_delay_seconds=1)
fire_locations = {}

if viirs:
    fire_points = viirs.map(lambda img: img.gt(330).selfMask().addBands(img).reduceToVectors(
        geometry=region, scale=1000, geometryType='centroid', labelProperty='fire', reducer=ee.Reducer.mean())).flatten()
    try:
        fire_list = fire_points.getInfo()['features']
        for f in fire_list:
            coords = f['geometry']['coordinates']
            lon_f, lat_f = coords
            name = f"{lat_f:.2f}, {lon_f:.2f}"
            try:
                loc_info = reverse((lat_f, lon_f), language='en')
                if loc_info:
                    name = loc_info.address
            except:
                pass
            fire_locations[name] = (lat_f, lon_f)
    except:
        pass

if fire_locations:
    selected_place = st.selectbox("📍 Select Fire Location", list(fire_locations.keys()))
    selected_coords = fire_locations[selected_place]
else:
    selected_coords = (lat, lon)

with st.sidebar:
    weather = get_weather(*selected_coords)
    if weather:
        st.header("☁️ Weather Conditions:")
        st.metric("🌡 Temperature", f"{weather['temperature']} °C")
        st.metric("💧 Humidity", f"{weather['humidity']}%")
        st.metric("🌬 Wind Speed", f"{weather['wind_speed']} m/s")
        st.metric("🧭 Wind Direction", f"{weather['wind_dir']} ({weather['wind_deg']}°)")
    else:
        st.error("⚠️ No weather data")

map_theme = "CartoDB dark_matter" if is_dark_mode else "CartoDB positron"
m = folium.Map(location=selected_coords, zoom_start=9, control_scale=True, tiles=map_theme)
folium.TileLayer(map_theme).add_to(m)
viirs_vis = {'min': 300, 'max': 400, 'palette': ['black', 'red', 'orange', 'yellow']}
folium.raster_layers.TileLayer(
    tiles=viirs_mean.select("Bright_ti4").visualize(**viirs_vis).getMapId()['tile_fetcher'].url_format,
    attr="VIIRS NOAA20 NRT", name="Fire Alerts", overlay=True, control=True).add_to(m)

for coords in fire_locations.values():
    folium.Marker(location=coords, icon=folium.Icon(color='red', icon='fire', prefix='fa')).add_to(m)

weather = get_weather(*selected_coords)

today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
today_end = datetime.now(timezone.utc)

viirs_today = viirs_raw.filterDate(today_start.isoformat(), today_end.isoformat())
viirs_today_count = viirs_today.size().getInfo()
viirs_has_today = viirs_today_count > 0

if fire_locations and weather and days_option == "Only Today (Real-Time)":
    elevation_img = ee.Image('USGS/SRTMGL1_003')

    prediction_features = {
        'NDVI': float(ndvi_img.reduceRegion(ee.Reducer.mean(), region, 500, bestEffort=True, maxPixels=1e8).get('NDVI').getInfo() or 0),
        'elevation': float(elevation_img.reduceRegion(ee.Reducer.mean(), region, 500, bestEffort=True, maxPixels=1e8).get('elevation').getInfo() or 0),
        'temperature_2m': float(weather['temperature']),
        'u_component_of_wind_10m': float(weather['wind_speed']),
        'v_component_of_wind_10m': float(weather['wind_speed']),
        'frp': float(viirs_mean.reduceRegion(ee.Reducer.mean(), region, 500, bestEffort=True, maxPixels=1e8).get('Bright_ti4').getInfo() or 0),
        'FireConfidence': 50.0,
        'BrightTi4': float(viirs_mean.reduceRegion(ee.Reducer.mean(), region, 500, bestEffort=True, maxPixels=1e8).get('Bright_ti4').getInfo() or 0),
        'BrightTi5': float(viirs_mean.reduceRegion(ee.Reducer.mean(), region, 500, bestEffort=True, maxPixels=1e8).get('Bright_ti5').getInfo() or 0)
    }

    input_df = pd.DataFrame([[prediction_features[feat] for feat in prediction_features]], columns=prediction_features.keys())
    prediction = model.predict(input_df)[0]

    st.subheader("📊 Wildfire Spread Prediction")
    st.success(f"🔥 Predicted Burned Area: {prediction:.2f} sq.km")
    st.info(f"🧭 Spread Direction: {weather['wind_dir']} ({weather['wind_deg']}°)")

    sector_coords = get_sector_points(selected_coords, weather['wind_deg'])
    folium.Polygon(locations=sector_coords, color='orange', fill=True, fill_opacity=0.3).add_to(m)
    end_lat, end_lon = compute_endpoint(*selected_coords, weather['wind_deg'])
    folium.PolyLine(locations=[selected_coords, (end_lat, end_lon)], color='silver', weight=5, dash_array='5').add_to(m)
    folium.RegularPolygonMarker(location=(end_lat, end_lon), number_of_sides=3, rotation=weather['wind_deg'], radius=8, color='black', fill_color='silver').add_to(m)

st.subheader("🗺 Wildfire Detection Map")
st_folium(m, width=1000, height=600)