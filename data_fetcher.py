"""
Data fetcher module for tide, wind, and wave information.
Uses free APIs: NOAA CO-OPS for tides, Open-Meteo for wind and waves.
"""
import requests
from datetime import datetime, timedelta
import pandas as pd
from typing import Dict, List, Optional
import time


class WeatherDataFetcher:
    """Fetches weather data for crabbing conditions."""

    def __init__(self):
        self.noaa_base_url = "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter"
        self.marine_base_url = "https://marine-api.open-meteo.com/v1/marine"

    def get_noaa_station_id(self, lat: float, lon: float) -> Optional[str]:
        """
        Get nearest NOAA tide station for given coordinates.
        This is a simplified mapping - in production, you'd query NOAA's station API.
        """
        # Common stations (station_id: (lat, lon, name))
        stations = {
            "9414290": (37.8063, -122.4659, "San Francisco, CA"),
            "9410230": (32.7150, -117.1733, "La Jolla, CA"),
            "9447130": (47.6062, -122.3321, "Seattle, WA"),
            "8454000": (41.5043, -71.3261, "Newport, RI"),
            "8518750": (40.4667, -74.0092, "The Battery, NY"),
            "8720218": (26.7153, -80.0533, "Lake Worth Pier, FL"),
            "8638610": (36.9467, -76.3300, "Sewells Point, VA"),
        }

        # Find nearest station
        min_dist = float('inf')
        nearest_station = "9414290"  # Default to San Francisco

        for station_id, (s_lat, s_lon, name) in stations.items():
            dist = ((lat - s_lat) ** 2 + (lon - s_lon) ** 2) ** 0.5
            if dist < min_dist:
                min_dist = dist
                nearest_station = station_id

        return nearest_station

    def fetch_tide_data(self, lat: float, lon: float, start_date: datetime, end_date: datetime) -> tuple[pd.DataFrame, bool]:
        """
        Fetch tide predictions from NOAA CO-OPS API.

        Args:
            lat: Latitude
            lon: Longitude
            start_date: Start date for predictions
            end_date: End date for predictions

        Returns:
            Tuple of (DataFrame with tide predictions, is_real_data bool)
        """
        station_id = self.get_noaa_station_id(lat, lon)

        params = {
            "product": "predictions",
            "application": "TideHunter",
            "begin_date": start_date.strftime("%Y%m%d"),
            "end_date": end_date.strftime("%Y%m%d"),
            "datum": "MLLW",
            "station": station_id,
            "time_zone": "lst_ldt",
            "units": "english",
            "interval": "h",  # Hourly data
            "format": "json"
        }

        try:
            response = requests.get(self.noaa_base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if "predictions" in data:
                df = pd.DataFrame(data["predictions"])
                df["t"] = pd.to_datetime(df["t"])
                df["v"] = pd.to_numeric(df["v"])
                df.rename(columns={"t": "datetime", "v": "tide_height"}, inplace=True)
                return df, True  # Real data!
            else:
                # Return empty dataframe if no data
                return pd.DataFrame(columns=["datetime", "tide_height"]), False

        except Exception as e:
            print(f"Error fetching tide data: {e}")
            # Return dummy data for demonstration
            return self._generate_dummy_tide_data(start_date, end_date), False

    def fetch_marine_data(self, lat: float, lon: float, start_date: datetime, end_date: datetime) -> tuple[pd.DataFrame, bool]:
        """
        Fetch wind and wave data from Open-Meteo Marine API.

        Args:
            lat: Latitude
            lon: Longitude
            start_date: Start date
            end_date: End date

        Returns:
            Tuple of (DataFrame with marine conditions, is_real_data bool)
        """
        params = {
            "latitude": lat,
            "longitude": lon,
            "hourly": "wave_height,wave_direction,wind_wave_height,wind_speed_10m,wind_direction_10m",
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "timezone": "auto"
        }

        try:
            response = requests.get(self.marine_base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if "hourly" in data:
                hourly = data["hourly"]
                df = pd.DataFrame({
                    "datetime": pd.to_datetime(hourly["time"]),
                    "wave_height": hourly.get("wave_height", [0] * len(hourly["time"])),
                    "wave_direction": hourly.get("wave_direction", [0] * len(hourly["time"])),
                    "wind_speed": hourly.get("wind_speed_10m", [0] * len(hourly["time"])),
                    "wind_direction": hourly.get("wind_direction_10m", [0] * len(hourly["time"]))
                })
                return df, True  # Real data!
            else:
                return pd.DataFrame(columns=["datetime", "wave_height", "wave_direction", "wind_speed", "wind_direction"]), False

        except Exception as e:
            print(f"Error fetching marine data: {e}")
            # Return dummy data for demonstration
            return self._generate_dummy_marine_data(start_date, end_date), False

    def fetch_all_data(self, lat: float, lon: float, start_date: datetime, end_date: datetime) -> tuple[pd.DataFrame, dict]:
        """
        Fetch all weather data (tide, wind, waves) and combine into one DataFrame.

        Args:
            lat: Latitude
            lon: Longitude
            start_date: Start date
            end_date: End date

        Returns:
            Tuple of (Combined DataFrame with all weather data, metadata dict with data source info)
        """
        metadata = {
            "using_real_data": False,
            "tide_source": "simulated",
            "marine_source": "simulated",
            "errors": []
        }

        # Fetch tide data
        tide_df, tide_is_real = self.fetch_tide_data(lat, lon, start_date, end_date)

        # Update metadata based on actual API success
        if tide_is_real:
            metadata["tide_source"] = "NOAA CO-OPS API"
        else:
            metadata["tide_source"] = "simulated"

        # Fetch marine data
        marine_df, marine_is_real = self.fetch_marine_data(lat, lon, start_date, end_date)

        # Update metadata based on actual API success
        if marine_is_real:
            metadata["marine_source"] = "Open-Meteo API"
        else:
            metadata["marine_source"] = "simulated"

        # Merge dataframes
        if not tide_df.empty and not marine_df.empty:
            combined_df = pd.merge(tide_df, marine_df, on="datetime", how="outer")
        elif not tide_df.empty:
            combined_df = tide_df
        elif not marine_df.empty:
            combined_df = marine_df
        else:
            combined_df = pd.DataFrame()

        # Sort by datetime
        if not combined_df.empty:
            combined_df = combined_df.sort_values("datetime").reset_index(drop=True)
            # Fill missing values
            combined_df = combined_df.ffill().fillna(0)

        # Determine if using real data
        if tide_is_real or marine_is_real:
            metadata["using_real_data"] = True
        else:
            metadata["using_real_data"] = False

        return combined_df, metadata

    def _generate_dummy_tide_data(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Generate dummy tide data for demonstration."""
        import numpy as np

        hours = []
        current = start_date
        while current <= end_date:
            hours.append(current)
            current += timedelta(hours=1)

        # Simulate tide with sinusoidal pattern (2 highs and 2 lows per day)
        tide_heights = []
        for i, dt in enumerate(hours):
            # 12.42 hour tidal period (semi-diurnal tide)
            hour_of_tide = (i * 1.0) / 12.42
            tide = 3.0 + 2.5 * np.sin(2 * np.pi * hour_of_tide)
            tide_heights.append(tide)

        return pd.DataFrame({
            "datetime": hours,
            "tide_height": tide_heights
        })

    def _generate_dummy_marine_data(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """
        Generate realistic dummy marine data for demonstration.
        Includes time-based variations to simulate real weather patterns.
        """
        import numpy as np

        hours = []
        current = start_date
        while current <= end_date:
            hours.append(current)
            current += timedelta(hours=1)

        # Use time-based seed for variety across different runs
        time_seed = int(start_date.timestamp()) % 10000
        np.random.seed(time_seed)

        # Generate realistic weather patterns with daily cycles
        wave_heights = []
        wind_speeds = []
        wind_directions = []
        wave_directions = []

        # Base values with realistic variation
        for i, dt in enumerate(hours):
            hour = dt.hour

            # Wind typically picks up during day (10am-4pm), calmer at night
            daily_wind_factor = 1.0 + 0.3 * np.sin((hour - 6) * np.pi / 12)
            base_wind = np.random.uniform(6, 15) * daily_wind_factor
            wind_speeds.append(max(2, base_wind))  # Min 2 mph wind

            # Waves influenced by wind with some lag
            wave_factor = 0.8 + 0.4 * np.sin((hour - 8) * np.pi / 12)
            base_wave = np.random.uniform(1.5, 3.5) * wave_factor
            wave_heights.append(max(0.5, base_wave))  # Min 0.5 ft waves

            # Prevailing wind direction (NW = 315°) with variation
            wind_dir = (315 + np.random.uniform(-45, 45)) % 360
            wind_directions.append(wind_dir)

            # Wave direction similar to wind direction
            wave_dir = (wind_dir + np.random.uniform(-30, 30)) % 360
            wave_directions.append(wave_dir)

        return pd.DataFrame({
            "datetime": hours,
            "wave_height": wave_heights,
            "wave_direction": wave_directions,
            "wind_speed": wind_speeds,
            "wind_direction": wind_directions
        })

    def fetch_ndbc_buoy_data(self, buoy_id: str) -> Optional[Dict]:
        """
        Fetch real-time data from NOAA NDBC buoy.

        Args:
            buoy_id: NDBC buoy station ID (e.g., "46026" for San Francisco)

        Returns:
            Dict with current conditions or None if unavailable
        """
        # NDBC provides real-time buoy data
        # Station 46026: San Francisco (37.759 N 122.833 W)
        # Station 46012: Half Moon Bay (37.361 N 122.881 W)
        url = f"https://www.ndbc.noaa.gov/data/realtime2/{buoy_id}.txt"

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            # Parse the data (space-separated values)
            lines = response.text.strip().split('\n')
            if len(lines) < 3:
                return None

            headers = lines[0].split()
            units = lines[1].split()
            latest = lines[2].split()

            # Build data dictionary
            data = {}
            for i, header in enumerate(headers):
                if i < len(latest):
                    try:
                        value = float(latest[i]) if latest[i] != 'MM' else None
                        data[header] = value
                    except ValueError:
                        data[header] = latest[i]

            # Extract key measurements
            result = {
                "wind_speed_mps": data.get("WSPD"),  # m/s
                "wind_direction": data.get("WDIR"),  # degrees
                "wave_height_m": data.get("WVHT"),   # meters
                "dominant_period": data.get("DPD"),  # seconds
                "atmospheric_pressure": data.get("PRES"),  # hPa
                "water_temp": data.get("WTMP"),      # Celsius
            }

            # Convert to imperial units
            if result["wind_speed_mps"]:
                result["wind_speed_mph"] = result["wind_speed_mps"] * 2.237  # m/s to mph
            if result["wave_height_m"]:
                result["wave_height_ft"] = result["wave_height_m"] * 3.281  # m to ft

            return result

        except Exception as e:
            print(f"Error fetching NDBC buoy {buoy_id}: {e}")
            return None

    def get_nearest_buoy(self, lat: float, lon: float) -> Optional[str]:
        """Get nearest NDBC buoy ID for given coordinates."""
        # Major buoys (buoy_id: (lat, lon, name))
        buoys = {
            "46026": (37.759, -122.833, "San Francisco"),
            "46012": (37.361, -122.881, "Half Moon Bay"),
            "46013": (38.238, -123.317, "Bodega Bay"),
            "46214": (39.225, -123.967, "Point Arena"),
            "46028": (35.741, -121.884, "Cape San Martin"),
            "46025": (33.749, -119.053, "Santa Monica Basin"),
            "46086": (32.491, -118.034, "San Clemente"),
        }

        min_dist = float('inf')
        nearest_buoy = None

        for buoy_id, (b_lat, b_lon, name) in buoys.items():
            dist = ((lat - b_lat) ** 2 + (lon - b_lon) ** 2) ** 0.5
            if dist < min_dist:
                min_dist = dist
                nearest_buoy = buoy_id

        return nearest_buoy
