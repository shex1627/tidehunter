# 🦀 TideHunter - Crabbing Forecast App

A Streamlit web application that provides hourly crabbing scores (1-10) based on tide, wind, and wave conditions. Perfect for planning your crabbing trips!

## Features

- **📊 Hourly Crabbing Scores**: Get scores from 1-10 for each hour based on environmental conditions
- **🗓️ Week-to-Week View**: Visual heatmap showing the best times to go crabbing over the next week
- **📍 Multiple Locations**: Add and manage multiple crabbing locations with custom coordinates
- **🌊 Real-time Data**: Fetches live tide data from NOAA and marine conditions from Open-Meteo
- **📈 Detailed Conditions**: View tide heights, wind speeds, and wave heights over time
- **🎯 Smart Scoring**: Algorithm considers tide height, tide movement, wind, waves, and time of day

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/tidehunter.git
cd tidehunter
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. (Optional) Copy environment variables:
```bash
cp .env.example .env
```

## Usage

1. Start the Streamlit app:
```bash
streamlit run app.py
```

2. Open your browser to the URL shown (typically `http://localhost:8501`)

3. Use the app:
   - **Select a location** from the sidebar dropdown
   - **Add new locations** using the form in the sidebar (provide name, latitude, longitude)
   - **Click "Fetch Latest Forecast"** to load data
   - **View the heatmap** to see the best crabbing times at a glance
   - **Scroll down** to see detailed hourly conditions

## Data Sources

### Live APIs (when internet accessible)

- **NOAA CO-OPS API**: Tide predictions for US coastal areas (FREE, no API key)
- **Open-Meteo**: Wind and marine conditions (FREE, no API key)
- **NDBC Buoys**: Real-time buoy data from NOAA (FREE, no API key)

### Fallback Demo Data

When APIs are unavailable (blocked network, offline), the app uses realistic simulated data:
- **Tide**: Sinusoidal pattern matching semi-diurnal tides
- **Wind**: 5-18 mph with daily variation (calmer at night, picks up midday)
- **Waves**: 0.5-4 ft correlated with wind patterns
- **Time-based seed**: Different runs produce varied but realistic patterns

**Note**: If you see "Error fetching..." messages in console, the app is using simulated data.

## How It Works

### Scoring Algorithm

The crabbing score (1-10) is calculated based on these factors:

1. **Tide Height (0-3 points)**
   - Ideal range: 2-4 feet
   - Lower tides often provide better access to crabbing areas
   - Bonus for moving tides (incoming/outgoing)

2. **Wind Speed (0-3 points)**
   - Ideal: < 10 mph
   - Poor: > 25 mph
   - Lower wind = calmer conditions and easier crabbing

3. **Wave Height (0-3 points)**
   - Ideal: < 2 feet
   - Poor: > 6 feet
   - Lower waves = safer and more comfortable

4. **Time of Day Bonus (0-1 point)**
   - Prime hours: Dawn (5-7 AM) and Dusk (5-7 PM)
   - Crabs are often more active during these times

### Data Sources

- **Tide Data**: NOAA CO-OPS API (tides and currents)
- **Marine Data**: Open-Meteo Marine API (wind and waves)

Both APIs are free and don't require API keys!

## Finding Coordinates

To add a new location, you need latitude and longitude:

1. Go to [Google Maps](https://maps.google.com)
2. Right-click on your desired location
3. Click the coordinates to copy them
4. Enter them in the "Add Location" form in the app

### Popular Crabbing Locations (US)

| Location | Latitude | Longitude |
|----------|----------|-----------|
| San Francisco Bay, CA | 37.8063 | -122.4659 |
| Bodega Bay, CA | 38.3333 | -123.0500 |
| Half Moon Bay, CA | 37.4636 | -122.4286 |
| Newport, OR | 44.6368 | -124.0538 |
| Seattle, WA | 47.6062 | -122.3321 |
| Charleston, OR | 43.3457 | -124.3221 |

## Project Structure

```
tidehunter/
├── app.py                 # Main Streamlit application
├── data_fetcher.py        # Fetches tide, wind, and wave data
├── crabbing_score.py      # Scoring algorithm
├── requirements.txt       # Python dependencies
├── .env.example          # Example environment variables
├── locations.json        # Saved locations (created automatically)
└── README.md            # This file
```

## Customization

### Adjusting Scoring Parameters

Edit `crabbing_score.py` to modify the scoring algorithm:

```python
# In CrabbingScoreCalculator.__init__()
self.ideal_tide_range = (2.0, 4.0)  # feet
self.ideal_wind_speed = 10.0        # mph
self.ideal_wave_height = 2.0        # feet
self.prime_hours = [5, 6, 7, 17, 18, 19]  # hours
```

### Adding More NOAA Stations

Edit the `get_noaa_station_id()` method in `data_fetcher.py` to add more tide stations:

```python
stations = {
    "STATION_ID": (latitude, longitude, "Name"),
    # Add more stations here
}
```

Find NOAA station IDs at: https://tidesandcurrents.noaa.gov/

## Data Validation

To verify data accuracy when running with internet access:

### Check Live Sources

Compare app forecasts against these trusted sources:

1. **NOAA Tides**: https://tidesandcurrents.noaa.gov/
2. **Tide-Forecast.com**: https://www.tide-forecast.com/
3. **Surf-Forecast.com**: https://www.surf-forecast.com/
4. **NDBC Buoys**: https://www.ndbc.noaa.gov/

### Wind Data Quality

The app shows realistic wind variations:
- **Range**: 2-20 mph typically
- **Pattern**: Calmer at night (5-8 mph), picks up midday (10-18 mph)
- **Direction**: Prevailing NW winds (270-360°) for Pacific coast

**If wind shows as 0 or constant**: You may be viewing cached/old data. Refresh the forecast.

### Test Scripts

Run validation tests:

```bash
# Test data quality
python test_improved_data.py

# Test specific locations
python test_locations.py

# Debug API responses
python debug_api.py
```

## Troubleshooting

### No data showing up

- Check your internet connection
- Verify that the coordinates are correct (latitude/longitude)
- Try a different location - some areas may not have nearby NOAA tide stations
- Check console for error messages

### API Errors

If you encounter API errors:
- NOAA API may be temporarily down - try again later
- Open-Meteo may have rate limits - wait a few minutes
- The app will use dummy data if APIs fail (for demonstration)

## Development

### Running Tests

```bash
# Install dev dependencies
pip install pytest pytest-cov

# Run tests (when available)
pytest
```

### Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is provided as-is for educational and informational purposes.

## Disclaimer

⚠️ **Important**: This app is for informational purposes only. Always:
- Check local crabbing regulations and seasons
- Verify safety conditions before heading out
- Consult official weather and marine forecasts
- Follow all local fishing and wildlife guidelines

## Credits

- Built with [Streamlit](https://streamlit.io/)
- Tide data from [NOAA CO-OPS](https://tidesandcurrents.noaa.gov/)
- Marine data from [Open-Meteo](https://open-meteo.com/)
- Created for crabbing enthusiasts 🦀

## Support

Found a bug or have a feature request? Please open an issue on GitHub!

Happy crabbing! 🦀🌊
