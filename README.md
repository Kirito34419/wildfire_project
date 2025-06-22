# wildfire_project
🔥 Global Wildfire Risk & Real-Time Fire Alert System

Overview:
----------
This project is a Streamlit-based web application designed to monitor, analyze, and predict wildfires in real time across the globe. It combines satellite data from Google Earth Engine with live weather data and a trained machine learning model to identify areas prone to fires and visualize predicted fire spread directions.

Key Features:
--------------
- 🌍 Real-time fire alerts from VIIRS (NOAA-20 satellite)
- 🌱 NDVI-based vegetation dryness analysis (MODIS data)
- 🧠 Wildfire spread prediction using a trained Random Forest model
- 🌬 Integrated weather data from OpenWeather API
- 🗺️ Interactive map built with Folium and customizable location input
- 💡 Dark Mode toggle and adjustable analysis radius
- 📈 Visual overlay of current fires, fire risk zones, wind-based spread predictions

Dependencies:
--------------
To run this project, make sure the following Python libraries are installed:

- streamlit
- earthengine-api
- folium
- streamlit-folium
- geopy
- requests
- joblib
- pandas
- numpy
- streamlit-extras

Install all using pip:

pip install streamlit earthengine-api folium streamlit-folium geopy requests joblib pandas numpy streamlit-extras

Setup Instructions:
--------------------
1. Clone the repository:
   git clone https://github.com/Kirito34419/wildfire_project.git
   cd wildfire-detection-app

2. Authenticate Google Earth Engine:
   earthengine authenticate

3. Add your OpenWeather API Key:
   In the main Python file, replace the placeholder with your API key:
   OPENWEATHER_API_KEY = "your_api_key_here"

4. Place your trained model in a `models` folder:
   The file should be named: wildfire_rf_model.pkl

5. Launch the app:
   streamlit run app.py

Model Details:
---------------
- Model: Random Forest Regression
- Input Features:
    - NDVI (vegetation index)
    - Elevation
    - Temperature
    - Wind Speed & Direction
    - Fire Radiative Power (FRP)
    - Brightness Temperatures (VIIRS bands)
- Output: Predicted burned area (in square kilometers)

Fire Spread Visualization:
---------------------------
- 🔴 Red Markers: Real-time fire alerts
- 🟠 Orange Sector: Predicted direction and area of spread based on wind
- ➡️ Silver Arrow: Wind-based spread direction vector

Data Sources:
--------------
- MODIS Burned Area: MODIS/061/MCD64A1
- MODIS NDVI: MODIS/061/MOD13Q1
- VIIRS NOAA-20: NASA/LANCE/NOAA20_VIIRS/C2
- Elevation: USGS/SRTMGL1_003
- Weather: OpenWeather API

Notes:
-------
- Geocoding and reverse-geocoding is powered by Geopy (Nominatim)
- Earth Engine region is dynamically computed based on user-input location and radius
- The app is modular and expandable, allowing future enhancements like historical fire patterns, user-defined zones, etc.

License:
---------
This project is intended for academic and educational purposes. Please update the license as appropriate for your usage.

Developer Notes:
-----------------
This system was built as part of a college project to demonstrate the real-world integration of satellite data, weather APIs, and machine learning into an interactive web app using Python. Contributions and feedback are welcome!

