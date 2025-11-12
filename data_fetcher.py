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

    def fetch_tide_data(self, lat: float, lon: float, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """
        Fetch tide predictions from NOAA CO-OPS API.

        Args:
            lat: Latitude
            lon: Longitude
            start_date: Start date for predictions
            end_date: End date for predictions

        Returns:
            DataFrame with tide predictions
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
                return df
            else:
                # Return empty dataframe if no data
                return pd.DataFrame(columns=["datetime", "tide_height"])

        except Exception as e:
            print(f"Error fetching tide data: {e}")
            # Return dummy data for demonstration
            return self._generate_dummy_tide_data(start_date, end_date)

    def fetch_marine_data(self, lat: float, lon: float, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """
        Fetch wind and wave data from Open-Meteo Marine API.

        Args:
            lat: Latitude
            lon: Longitude
            start_date: Start date
            end_date: End date

        Returns:
            DataFrame with marine conditions
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
                return df
            else:
                return pd.DataFrame(columns=["datetime", "wave_height", "wave_direction", "wind_speed", "wind_direction"])

        except Exception as e:
            print(f"Error fetching marine data: {e}")
            # Return dummy data for demonstration
            return self._generate_dummy_marine_data(start_date, end_date)

    def fetch_all_data(self, lat: float, lon: float, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """
        Fetch all weather data (tide, wind, waves) and combine into one DataFrame.

        Args:
            lat: Latitude
            lon: Longitude
            start_date: Start date
            end_date: End date

        Returns:
            Combined DataFrame with all weather data
        """
        # Fetch tide data
        tide_df = self.fetch_tide_data(lat, lon, start_date, end_date)

        # Fetch marine data
        marine_df = self.fetch_marine_data(lat, lon, start_date, end_date)

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
            combined_df = combined_df.fillna(method='ffill').fillna(0)

        return combined_df

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
        """Generate dummy marine data for demonstration."""
        import numpy as np

        hours = []
        current = start_date
        while current <= end_date:
            hours.append(current)
            current += timedelta(hours=1)

        # Generate realistic-looking random data
        np.random.seed(42)
        wave_heights = np.random.uniform(1, 4, len(hours))
        wave_directions = np.random.uniform(0, 360, len(hours))
        wind_speeds = np.random.uniform(5, 20, len(hours))
        wind_directions = np.random.uniform(0, 360, len(hours))

        return pd.DataFrame({
            "datetime": hours,
            "wave_height": wave_heights,
            "wave_direction": wave_directions,
            "wind_speed": wind_speeds,
            "wind_direction": wind_directions
        })
