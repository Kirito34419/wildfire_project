import requests
from dotenv import load_dotenv
import os

# Load .env credentials
load_dotenv()
username = os.getenv('unknownjdwowq')
password = os.getenv("'atW;'H:7Wi%B88")

def download_firms_data():
    url = "https://firms.modaps.eosdis.nasa.gov/api/country/csv/SUOMI_VIIRS_SNPP_NRT/world/1/VIIRS_SNPP_NRT_Global_24h.csv"

    output_file = "latest_fire_data.csv"

    try:
        print("⬇️ Downloading fire data...")
        response = requests.get(url, auth=(username, password))

        if response.status_code == 200:
            with open(output_file, "wb") as f:
                f.write(response.content)
            print(f"✅ Downloaded to: {output_file}")
        else:
            print(f"❌ Failed to download. Status code: {response.status_code}")
            print(response.text)
    except Exception as e:
        print("❌ Error:", e)

download_firms_data()
