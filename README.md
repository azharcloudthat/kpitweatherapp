# KPIT Weather App

A simple Flask weather dashboard that shows current conditions and a five-day forecast for a city using the Open-Meteo APIs.

## Features
- Search weather by city name
- View current temperature, humidity, wind, and precipitation
- View five-day forecast with condition labels
- Friendly error messages for invalid city or provider issues

## Tech Stack
- Python
- Flask
- Vanilla JavaScript, HTML, CSS

## Prerequisites
- Python 3.10+ (recommended)

## Setup
1. Clone the repository.
2. Create and activate a virtual environment.
3. Install dependencies:

```bash
pip install -r requirements.txt
```

## Run the app

```bash
python app.py
```

Open `http://127.0.0.1:5000` in your browser.

## API Endpoint
- `GET /weather?city=<city-name>`

Returns weather data as JSON or an error message.
