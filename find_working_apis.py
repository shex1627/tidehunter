"""
Find working data sources for tide, wind, and wave data.
Tests multiple alternatives to blocked APIs.
"""
import requests
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET
import json


def test_noaa_xml():
    """Test NOAA XML endpoint."""
    print("="*70)
    print("Testing NOAA XML API")
    print("="*70)

    station_id = "9414290"  # San Francisco
    start = datetime.now()
    end = start + timedelta(days=1)

    # Try XML format instead of JSON
    url = "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter"
    params = {
        "product": "predictions",
        "begin_date": start.strftime("%Y%m%d"),
        "end_date": end.strftime("%Y%m%d"),
        "datum": "MLLW",
        "station": station_id,
        "time_zone": "lst_ldt",
        "units": "english",
        "interval": "h",
        "format": "xml"  # Try XML instead of JSON
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print(f"✅ SUCCESS! XML endpoint works")
            print(f"Response length: {len(response.text)} characters")
            print(f"First 500 chars:\n{response.text[:500]}")
            return True
        else:
            print(f"❌ Failed: {response.status_code}")
            print(f"Response: {response.text[:200]}")
    except Exception as e:
        print(f"❌ Error: {e}")

    return False


def test_noaa_csv():
    """Test NOAA CSV endpoint."""
    print("\n" + "="*70)
    print("Testing NOAA CSV API")
    print("="*70)

    station_id = "9414290"
    start = datetime.now()
    end = start + timedelta(days=1)

    url = "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter"
    params = {
        "product": "predictions",
        "begin_date": start.strftime("%Y%m%d"),
        "end_date": end.strftime("%Y%m%d"),
        "datum": "MLLW",
        "station": station_id,
        "time_zone": "lst_ldt",
        "units": "english",
        "interval": "h",
        "format": "csv"  # Try CSV
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print(f"✅ SUCCESS! CSV endpoint works")
            lines = response.text.split('\n')
            print(f"Lines: {len(lines)}")
            print(f"First 5 lines:")
            for line in lines[:5]:
                print(f"  {line}")
            return True
        else:
            print(f"❌ Failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")

    return False


def test_wttr_weather():
    """Test wttr.in weather API (free, no key needed)."""
    print("\n" + "="*70)
    print("Testing wttr.in Weather API")
    print("="*70)

    # wttr.in is a free weather service
    location = "Pacifica,CA"
    url = f"https://wttr.in/{location}?format=j1"

    try:
        response = requests.get(url, timeout=10)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ SUCCESS! wttr.in works")

            if 'current_condition' in data:
                current = data['current_condition'][0]
                print(f"\nCurrent conditions:")
                print(f"  Wind: {current.get('windspeedMiles', 'N/A')} mph")
                print(f"  Wind Dir: {current.get('winddir16Point', 'N/A')}")
                print(f"  Temp: {current.get('temp_F', 'N/A')}°F")

            if 'weather' in data:
                print(f"\nForecast available: {len(data['weather'])} days")

            return True
        else:
            print(f"❌ Failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")

    return False


def test_weather_gov():
    """Test weather.gov API (NOAA National Weather Service)."""
    print("\n" + "="*70)
    print("Testing weather.gov API")
    print("="*70)

    # NWS API - free, no key needed
    lat, lon = 37.6138, -122.4872  # Pacifica

    try:
        # First get grid point
        url = f"https://api.weather.gov/points/{lat},{lon}"
        headers = {"User-Agent": "TideHunter/1.0"}

        response = requests.get(url, headers=headers, timeout=10)
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"✅ SUCCESS! weather.gov API works")

            if 'properties' in data:
                props = data['properties']
                print(f"\nLocation: {props.get('relativeLocation', {}).get('properties', {}).get('city', 'N/A')}")
                print(f"Grid: {props.get('gridId', 'N/A')}")
                print(f"Forecast URL: {props.get('forecast', 'N/A')[:60]}...")

                # Try to get forecast
                forecast_url = props.get('forecast')
                if forecast_url:
                    forecast_resp = requests.get(forecast_url, headers=headers, timeout=10)
                    if forecast_resp.status_code == 200:
                        forecast = forecast_resp.json()
                        if 'properties' in forecast and 'periods' in forecast['properties']:
                            periods = forecast['properties']['periods']
                            print(f"\nForecast periods: {len(periods)}")
                            if len(periods) > 0:
                                first = periods[0]
                                print(f"  {first.get('name', 'N/A')}: {first.get('temperature', 'N/A')}°{first.get('temperatureUnit', 'F')}")
                                print(f"  Wind: {first.get('windSpeed', 'N/A')} {first.get('windDirection', 'N/A')}")

            return True
        else:
            print(f"❌ Failed: {response.status_code}")
            print(f"Response: {response.text[:200]}")
    except Exception as e:
        print(f"❌ Error: {e}")

    return False


def test_open_meteo_direct():
    """Test Open-Meteo with different parameters."""
    print("\n" + "="*70)
    print("Testing Open-Meteo Direct API")
    print("="*70)

    lat, lon = 37.6138, -122.4872

    # Try the main forecast API
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "wind_speed_10m,wind_direction_10m",
        "temperature_unit": "fahrenheit",
        "wind_speed_unit": "mph",
        "forecast_days": 7
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"✅ SUCCESS! Open-Meteo works")

            if 'hourly' in data:
                hourly = data['hourly']
                print(f"\nHourly data available:")
                print(f"  Time entries: {len(hourly.get('time', []))}")
                print(f"  Wind speed entries: {len(hourly.get('wind_speed_10m', []))}")

                if len(hourly.get('time', [])) > 0:
                    print(f"\nFirst 3 entries:")
                    for i in range(min(3, len(hourly['time']))):
                        print(f"  {hourly['time'][i]}: {hourly.get('wind_speed_10m', [])[i]} mph at {hourly.get('wind_direction_10m', [])[i]}°")

            return True
        else:
            print(f"❌ Failed: {response.status_code}")
            print(f"Response: {response.text[:200]}")
    except Exception as e:
        print(f"❌ Error: {e}")

    return False


def test_stormglass():
    """Test StormGlass.io API (has free tier)."""
    print("\n" + "="*70)
    print("Testing StormGlass.io API (marine data)")
    print("="*70)

    # Note: Requires API key, but has free tier
    lat, lon = 37.6138, -122.4872

    url = "https://api.stormglass.io/v2/weather/point"
    params = {
        "lat": lat,
        "lng": lon,
        "params": "waveHeight,windSpeed,windDirection"
    }

    # Try without key first to see if it's accessible
    try:
        response = requests.get(url, params=params, timeout=10)
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            print(f"✅ SUCCESS! StormGlass works")
            return True
        elif response.status_code == 401:
            print(f"⚠️  Requires API key (has free tier: 50 requests/day)")
            print(f"   Sign up at: https://stormglass.io/")
            return False
        else:
            print(f"❌ Failed: {response.status_code}")
            print(f"Response: {response.text[:200]}")
    except Exception as e:
        print(f"❌ Error: {e}")

    return False


def test_worldtides():
    """Test WorldTides API."""
    print("\n" + "="*70)
    print("Testing WorldTides API")
    print("="*70)

    lat, lon = 37.6138, -122.4872

    url = "https://www.worldtides.info/api/v3"
    params = {
        "heights": "",
        "lat": lat,
        "lon": lon,
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            print(f"✅ SUCCESS! WorldTides works")
            return True
        elif response.status_code == 402:
            print(f"⚠️  Requires API key (paid service)")
            return False
        else:
            print(f"❌ Status: {response.status_code}")
            print(f"Response: {response.text[:200]}")
    except Exception as e:
        print(f"❌ Error: {e}")

    return False


def test_usno_tides():
    """Test USNO tide data."""
    print("\n" + "="*70)
    print("Testing US Naval Observatory Tide Data")
    print("="*70)

    # USNO has astronomical data
    url = "https://aa.usno.navy.mil/api/rstt/oneday"
    params = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "coords": "37.6N,122.5W",
        "tz": -8
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            print(f"✅ SUCCESS! USNO API works")
            data = response.json()
            print(f"Data keys: {list(data.keys())}")
            return True
        else:
            print(f"❌ Failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")

    return False


def main():
    print("\n🔍 TESTING ALTERNATIVE DATA SOURCES\n")
    print("Finding working APIs for real tide, wind, and wave data...")
    print("="*70)

    results = {}

    # Test all sources
    results['NOAA XML'] = test_noaa_xml()
    results['NOAA CSV'] = test_noaa_csv()
    results['wttr.in'] = test_wttr_weather()
    results['weather.gov'] = test_weather_gov()
    results['Open-Meteo'] = test_open_meteo_direct()
    results['StormGlass'] = test_stormglass()
    results['WorldTides'] = test_worldtides()
    results['USNO'] = test_usno_tides()

    # Summary
    print("\n" + "="*70)
    print("SUMMARY - Working Data Sources")
    print("="*70)

    working = []
    needs_key = []
    failed = []

    for source, status in results.items():
        if status:
            working.append(source)
            print(f"✅ {source} - WORKS!")
        else:
            failed.append(source)
            print(f"❌ {source} - Not accessible")

    print(f"\n{'='*70}")
    if working:
        print(f"✅ FOUND {len(working)} WORKING SOURCE(S)!")
        print(f"\nWe can use these for real data:")
        for source in working:
            print(f"  - {source}")
    else:
        print(f"❌ NO WORKING SOURCES FOUND")
        print(f"\nAll tested APIs are blocked or require authentication.")
        print(f"Recommendations:")
        print(f"  1. Deploy to real server with internet access")
        print(f"  2. Use API key services (StormGlass, WorldTides)")
        print(f"  3. Implement web scraping as fallback")

    return working


if __name__ == "__main__":
    working_sources = main()
