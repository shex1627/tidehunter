"""
Debug script to check actual API responses and data quality.
"""
import requests
from datetime import datetime, timedelta
import json


def test_noaa_api():
    """Test NOAA tide API directly."""
    print("="*70)
    print("Testing NOAA Tide API")
    print("="*70)

    station_id = "9414290"  # San Francisco
    start_date = datetime.now()
    end_date = start_date + timedelta(days=1)

    url = "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter"
    params = {
        "product": "predictions",
        "application": "TideHunter",
        "begin_date": start_date.strftime("%Y%m%d"),
        "end_date": end_date.strftime("%Y%m%d"),
        "datum": "MLLW",
        "station": station_id,
        "time_zone": "lst_ldt",
        "units": "english",
        "interval": "h",
        "format": "json"
    }

    print(f"\nRequest URL: {url}")
    print(f"Parameters: {json.dumps(params, indent=2)}")

    try:
        response = requests.get(url, params=params, timeout=10)
        print(f"\nStatus Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")

        if response.status_code == 200:
            data = response.json()
            print(f"\nResponse Keys: {data.keys()}")
            if "predictions" in data:
                print(f"Number of predictions: {len(data['predictions'])}")
                print(f"\nFirst 3 predictions:")
                for pred in data['predictions'][:3]:
                    print(f"  {pred}")
            else:
                print(f"Full Response: {json.dumps(data, indent=2)}")
        else:
            print(f"Error Response: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")


def test_openmeteo_marine_api():
    """Test Open-Meteo Marine API directly."""
    print("\n" + "="*70)
    print("Testing Open-Meteo Marine API")
    print("="*70)

    lat, lon = 37.6138, -122.4872  # Pacifica
    start_date = datetime.now()
    end_date = start_date + timedelta(days=1)

    url = "https://marine-api.open-meteo.com/v1/marine"
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "wave_height,wave_direction,wind_wave_height,wind_speed_10m,wind_direction_10m",
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
        "timezone": "auto"
    }

    print(f"\nRequest URL: {url}")
    print(f"Parameters: {json.dumps(params, indent=2)}")

    try:
        response = requests.get(url, params=params, timeout=10)
        print(f"\nStatus Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"\nResponse Keys: {data.keys()}")

            if "hourly" in data:
                hourly = data["hourly"]
                print(f"\nHourly data keys: {hourly.keys()}")
                print(f"Number of time entries: {len(hourly.get('time', []))}")

                # Check first few entries
                print(f"\nFirst 3 hourly entries:")
                for i in range(min(3, len(hourly.get('time', [])))):
                    print(f"\n  Time: {hourly['time'][i]}")
                    print(f"  Wave Height: {hourly.get('wave_height', [None]*10)[i]}")
                    print(f"  Wind Speed 10m: {hourly.get('wind_speed_10m', [None]*10)[i]}")
                    print(f"  Wind Direction 10m: {hourly.get('wind_direction_10m', [None]*10)[i]}")
                    print(f"  Wave Direction: {hourly.get('wave_direction', [None]*10)[i]}")
            else:
                print(f"Full Response: {json.dumps(data, indent=2)[:500]}")
        else:
            print(f"Error Response: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")


def test_openmeteo_weather_api():
    """Test Open-Meteo Weather API for wind data."""
    print("\n" + "="*70)
    print("Testing Open-Meteo Weather API (for wind)")
    print("="*70)

    lat, lon = 37.6138, -122.4872  # Pacifica

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "wind_speed_10m,wind_direction_10m,wind_gusts_10m",
        "timezone": "auto",
        "forecast_days": 7
    }

    print(f"\nRequest URL: {url}")
    print(f"Parameters: {json.dumps(params, indent=2)}")

    try:
        response = requests.get(url, params=params, timeout=10)
        print(f"\nStatus Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"\nResponse Keys: {data.keys()}")

            if "hourly" in data:
                hourly = data["hourly"]
                print(f"\nHourly data keys: {hourly.keys()}")
                print(f"Number of time entries: {len(hourly.get('time', []))}")

                # Check first few entries
                print(f"\nFirst 5 hourly entries:")
                for i in range(min(5, len(hourly.get('time', [])))):
                    print(f"\n  Time: {hourly['time'][i]}")
                    print(f"  Wind Speed 10m: {hourly.get('wind_speed_10m', [None]*10)[i]} km/h")
                    print(f"  Wind Direction 10m: {hourly.get('wind_direction_10m', [None]*10)[i]}°")
                    print(f"  Wind Gusts 10m: {hourly.get('wind_gusts_10m', [None]*10)[i]} km/h")

                # Check for zeros
                wind_speeds = hourly.get('wind_speed_10m', [])
                zero_count = sum(1 for w in wind_speeds if w == 0 or w is None)
                print(f"\nWind data quality:")
                print(f"  Total entries: {len(wind_speeds)}")
                print(f"  Zero/None values: {zero_count}")
                print(f"  Non-zero values: {len(wind_speeds) - zero_count}")
                if len(wind_speeds) > 0:
                    non_zero = [w for w in wind_speeds if w and w > 0]
                    if non_zero:
                        print(f"  Min wind: {min(non_zero):.1f} km/h")
                        print(f"  Max wind: {max(non_zero):.1f} km/h")
                        print(f"  Avg wind: {sum(non_zero)/len(non_zero):.1f} km/h")
        else:
            print(f"Error Response: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")


def main():
    print("\n🔍 API Data Quality Check\n")

    # Test all APIs
    test_noaa_api()
    test_openmeteo_marine_api()
    test_openmeteo_weather_api()

    print("\n" + "="*70)
    print("✅ API testing complete")
    print("="*70)


if __name__ == "__main__":
    main()
