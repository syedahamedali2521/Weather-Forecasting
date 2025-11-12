import streamlit as st
import requests
import pandas as pd

try:
    import folium
    from streamlit_folium import st_folium
    FOLIUM_AVAILABLE = True
except ImportError:
    FOLIUM_AVAILABLE = False
    st.error("Please install Folium and Streamlit-Folium: pip install folium streamlit-folium")

# -------------------------------------------------------------------
# Helper Functions for API Calls
# -------------------------------------------------------------------

def get_location_coordinates(city_name):
    """Fetch coordinates from Open-Meteo Geocoding API."""
    url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {"name": city_name, "count": 1}
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        if "results" in data and len(data["results"]) > 0:
            loc = data["results"][0]
            return {
                "latitude": loc["latitude"],
                "longitude": loc["longitude"],
                "name": loc.get("name", city_name),
                "country": loc.get("country", ""),
            }
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching location: {e}")
        return None


def get_weather_data(lat, lon):
    """Fetch real-time weather data from Open-Meteo."""
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current_weather": "true",
        "temperature_unit": "celsius",
        "windspeed_unit": "kmh",
    }
    try:
        r = requests.get(url, params=params)
        r.raise_for_status()
        data = r.json()
        return data.get("current_weather", None)
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching weather: {e}")
        return None


def get_weather_forecast(lat, lon):
    """Fetch 5-day forecast."""
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": ["temperature_2m_max", "temperature_2m_min", "weathercode"],
        "timezone": "auto",
        "forecast_days": 5,
    }
    try:
        r = requests.get(url, params=params)
        r.raise_for_status()
        data = r.json()
        if "daily" in data:
            forecast = []
            for i in range(len(data["daily"]["time"])):
                forecast.append({
                    "date": pd.to_datetime(data["daily"]["time"][i]).strftime("%a %d"),
                    "temperature_max": data["daily"]["temperature_2m_max"][i],
                    "temperature_min": data["daily"]["temperature_2m_min"][i],
                    "weathercode": data["daily"]["weathercode"][i],
                })
            return forecast
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching forecast: {e}")
        return None


# -------------------------------------------------------------------
# Weather Symbols
# -------------------------------------------------------------------
WEATHER_SYMBOLS = {
    0: ("☀️", "Clear sky", "#FFD700"),
    1: ("🌤️", "Mainly clear", "#87CEEB"),
    2: ("🌥️", "Partly cloudy", "#A9A9A9"),
    3: ("☁️", "Overcast", "#696969"),
    45: ("🌫️", "Fog", "#708090"),
    61: ("🌧️", "Rain", "#4682B4"),
    71: ("🌨️", "Snow", "#E0FFFF"),
    95: ("⛈️", "Thunderstorm", "#4B0082"),
}

def get_weather_animation(code):
    if code in [71, 73, 75, 77, 85, 86]:
        st.snow()
    elif code in [95, 96, 99]:
        st.balloons()


# -------------------------------------------------------------------
# Streamlit Page Setup
# -------------------------------------------------------------------
st.set_page_config(page_title="Real-Time Weather", page_icon="🌦️", layout="wide")

# -------------------------------------------------------------------
# Force Dark Theme with Sky Blue Glow
# -------------------------------------------------------------------
st.markdown("""
<style>
html, body, [class*="stAppViewContainer"], [class*="stMain"], [data-testid="stAppViewContainer"],
[data-testid="stVerticalBlock"], [data-testid="stMarkdownContainer"] {
    background-color: #000000 !important;
    color: #e0f7fa !important;
}

/* Sidebar styling */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #000000 0%, #001a1a 100%) !important;
    border-right: 1px solid rgba(102, 252, 241, 0.2);
}
section[data-testid="stSidebar"] * {
    color: #66fcf1 !important;
}

/* Tabs, inputs */
div[data-baseweb="tab-list"] button, input, textarea {
    background-color: #0b0c10 !important;
    color: #ffffff !important;
    border: 1px solid #1f4068 !important;
}

/* Headings */
h1, h2, h3, h4, h5, h6 {
    color: #66fcf1 !important;
    text-shadow: 0px 0px 12px #00eaff;
}

/* Weather Cards */
.weather-card, .metric-card {
    background: rgba(10, 25, 47, 0.9);
    border-radius: 15px;
    padding: 20px;
    color: #ffffff;
    text-align: center;
    margin: 10px 0;
    box-shadow: 0 0 20px #1f4068;
}
.metric-card:hover, .forecast-card:hover {
    transform: scale(1.05);
    transition: 0.3s;
    box-shadow: 0 0 25px #00eaff;
}
.forecast-card {
    border-radius: 15px;
    padding: 15px;
    margin: 8px;
    text-align: center;
    color: white;
    box-shadow: 0 0 20px rgba(102,252,241,0.3);
}

/* Remove white containers */
[data-testid="stAppViewBlockContainer"], [data-testid="stVerticalBlock"], [data-testid="stHorizontalBlock"] {
    background-color: transparent !important;
}
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------------
# Main App
# -------------------------------------------------------------------
st.title("🌦️ Real-Time Weather Predictor")
st.subheader("Select Location")

tab1, tab2 = st.tabs(["🔍 Search by City", "🗺️ Select on Map"])

if "location_data" not in st.session_state:
    st.session_state["location_data"] = None

# Search tab
with tab1:
    city = st.text_input("Enter a city name:", placeholder="e.g., London, Tokyo, New York")
    if city:
        loc = get_location_coordinates(city)
        if loc:
            st.session_state["location_data"] = loc
            st.success(f"Selected: {loc['name']}, {loc['country']}")
        else:
            st.error("City not found.")

# Map tab
with tab2:
    if FOLIUM_AVAILABLE:
        m = folium.Map(location=[20, 0], zoom_start=2)
        m.add_child(folium.LatLngPopup())
        map_data = st_folium(m, height=400, width=700)
        if map_data and map_data.get("last_clicked"):
            lat = map_data["last_clicked"]["lat"]
            lon = map_data["last_clicked"]["lng"]
            st.session_state["location_data"] = {
                "latitude": lat,
                "longitude": lon,
                "name": f"{lat:.2f}, {lon:.2f}",
                "country": ""
            }
            st.success(f"Selected location: {lat:.2f}, {lon:.2f}")
    else:
        st.warning("Install folium and streamlit-folium to use map selection.")

# -------------------------------------------------------------------
# Weather Display
# -------------------------------------------------------------------
if st.session_state["location_data"]:
    loc = st.session_state["location_data"]
    st.subheader(f"Weather for {loc['name']}, {loc['country']}")

    data = get_weather_data(loc["latitude"], loc["longitude"])
    if data:
        temp = data["temperature"]
        wind = data["windspeed"]
        code = data["weathercode"]
        symbol, desc, color = WEATHER_SYMBOLS.get(code, ("❓", "Unknown", "#66fcf1"))

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"<div class='metric-card'><h3>🌡️ Temperature</h3><h1>{temp}°C</h1></div>", unsafe_allow_html=True)
        with col2:
            st.markdown(f"<div class='metric-card'><h3>💨 Wind Speed</h3><h1>{wind} km/h</h1></div>", unsafe_allow_html=True)
        with col3:
            st.markdown(f"<div class='weather-card' style='box-shadow:0 0 25px {color}; background:{color}33;'><p style='font-size:60px;'>{symbol}</p><h3>{desc}</h3></div>", unsafe_allow_html=True)

        get_weather_animation(code)

        # Forecast
        st.subheader("📅 5-Day Forecast")
        forecast = get_weather_forecast(loc["latitude"], loc["longitude"])
        if forecast:
            cols = st.columns(5)
            for i, day in enumerate(forecast[:5]):
                s, d, c = WEATHER_SYMBOLS.get(day["weathercode"], ("❓", "Unknown", "#66fcf1"))
                with cols[i]:
                    st.markdown(f"""
                    <div class='forecast-card' style='background:{c}33; box-shadow:0 0 15px {c};'>
                        <h4>{day['date']}</h4>
                        <p style='font-size:30px'>{s}</p>
                        <p>{day['temperature_max']}° / {day['temperature_min']}°C</p>
                        <small>{d}</small>
                    </div>
                    """, unsafe_allow_html=True)

        st.subheader("📍 Location Map")
        st.map(pd.DataFrame({"lat": [loc["latitude"]], "lon": [loc["longitude"]]}))
    else:
        st.error("Weather data unavailable.")

# -------------------------------------------------------------------
# Sidebar - About Section
# -------------------------------------------------------------------
st.sidebar.title("🌟 About")
st.sidebar.markdown("""
<div style='color:#66fcf1; text-shadow:0px 0px 15px #66fcf1;'>
<b>Real-Time Weather Predictor</b> 🌦️  
Powered by <b>Open-Meteo API</b>  

✨ <b>Features:</b><br>
🔍 Search by city<br>
🗺️ Map-based selection<br>
🌡️ Real-time data<br>
🎨 Dark neon UI<br>
🌈 Animated effects<br><br>

Built with ❤️ using Streamlit & Folium.</br><br>
Built by ❤️ Syed Ahamed Ali
</div>
""", unsafe_allow_html=True)
