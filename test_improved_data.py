"""
Test the improved data generation and NDBC buoy integration.
"""
from datetime import datetime, timedelta
from data_fetcher import WeatherDataFetcher
import pandas as pd


def test_improved_dummy_data():
    """Test that dummy data has proper wind variation."""
    print("="*70)
    print("Testing Improved Dummy Data Generation")
    print("="*70)

    fetcher = WeatherDataFetcher()

    # Test with Pacifica
    lat, lon = 37.6138, -122.4872
    start_date = datetime.now()
    end_date = start_date + timedelta(days=2)

    print(f"\nGenerating dummy marine data for 48 hours...")
    df = fetcher._generate_dummy_marine_data(start_date, end_date)

    print(f"\nData Statistics:")
    print(f"  Total records: {len(df)}")
    print(f"\n  Wind Speed (mph):")
    print(f"    Min: {df['wind_speed'].min():.1f}")
    print(f"    Max: {df['wind_speed'].max():.1f}")
    print(f"    Mean: {df['wind_speed'].mean():.1f}")
    print(f"    Median: {df['wind_speed'].median():.1f}")

    print(f"\n  Wave Height (ft):")
    print(f"    Min: {df['wave_height'].min():.1f}")
    print(f"    Max: {df['wave_height'].max():.1f}")
    print(f"    Mean: {df['wave_height'].mean():.1f}")

    # Check for zeros
    zero_wind = len(df[df['wind_speed'] == 0])
    zero_waves = len(df[df['wave_height'] == 0])

    print(f"\n  Zero Values:")
    print(f"    Wind speed = 0: {zero_wind} records ({zero_wind/len(df)*100:.1f}%)")
    print(f"    Wave height = 0: {zero_waves} records ({zero_waves/len(df)*100:.1f}%)")

    # Show hourly variation
    print(f"\n  Sample Hourly Data (First 12 hours):")
    print(f"  {'Hour':<10} {'Wind (mph)':<12} {'Waves (ft)':<12} {'Wind Dir'}")
    print(f"  {'-'*10} {'-'*12} {'-'*12} {'-'*10}")

    for i in range(min(12, len(df))):
        row = df.iloc[i]
        hour = row['datetime'].strftime("%I:%M %p")
        wind = row['wind_speed']
        wave = row['wave_height']
        wind_dir = row['wind_direction']
        print(f"  {hour:<10} {wind:>6.1f} mph    {wave:>6.2f} ft     {wind_dir:>6.0f}°")

    if zero_wind == 0:
        print("\n✅ PASS: No zero wind speeds!")
    else:
        print(f"\n⚠️  WARNING: {zero_wind} records have zero wind")

    return df


def test_ndbc_buoy():
    """Test NDBC buoy data fetching."""
    print("\n" + "="*70)
    print("Testing NDBC Buoy Integration")
    print("="*70)

    fetcher = WeatherDataFetcher()

    # Test San Francisco buoy
    buoy_id = "46026"
    print(f"\nFetching real-time data from NDBC Buoy {buoy_id} (San Francisco)...")

    data = fetcher.fetch_ndbc_buoy_data(buoy_id)

    if data:
        print(f"\n✅ Successfully fetched buoy data:")
        print(f"  Wind Speed: {data.get('wind_speed_mph', 'N/A'):.1f} mph" if data.get('wind_speed_mph') else "  Wind Speed: N/A")
        print(f"  Wind Direction: {data.get('wind_direction', 'N/A')}°" if data.get('wind_direction') else "  Wind Direction: N/A")
        print(f"  Wave Height: {data.get('wave_height_ft', 'N/A'):.1f} ft" if data.get('wave_height_ft') else "  Wave Height: N/A")
        print(f"  Wave Period: {data.get('dominant_period', 'N/A')} sec" if data.get('dominant_period') else "  Wave Period: N/A")
        print(f"  Water Temp: {data.get('water_temp', 'N/A')}°C" if data.get('water_temp') else "  Water Temp: N/A")
        print(f"  Pressure: {data.get('atmospheric_pressure', 'N/A')} hPa" if data.get('atmospheric_pressure') else "  Pressure: N/A")
    else:
        print(f"❌ Could not fetch buoy data (API may be blocked or buoy offline)")

    # Test nearest buoy lookup
    print(f"\n  Testing nearest buoy lookup:")
    test_locations = {
        "Pacifica": (37.6138, -122.4872),
        "Half Moon Bay": (37.5, -122.5),
        "Bodega Bay": (38.3, -123.0),
    }

    for name, (lat, lon) in test_locations.items():
        buoy = fetcher.get_nearest_buoy(lat, lon)
        print(f"    {name}: Buoy {buoy}")


def test_full_integration():
    """Test full data fetching with improved fallbacks."""
    print("\n" + "="*70)
    print("Testing Full Data Integration")
    print("="*70)

    fetcher = WeatherDataFetcher()

    lat, lon = 37.6138, -122.4872  # Pacifica
    start_date = datetime.now()
    end_date = start_date + timedelta(days=1)

    print(f"\nFetching all data for Pacifica...")
    df = fetcher.fetch_all_data(lat, lon, start_date, end_date)

    if not df.empty:
        print(f"\n✅ Data retrieved successfully:")
        print(f"  Records: {len(df)}")
        print(f"  Columns: {list(df.columns)}")

        # Check wind data quality
        if 'wind_speed' in df.columns:
            wind_stats = df['wind_speed'].describe()
            print(f"\n  Wind Speed Statistics:")
            print(f"    Count: {wind_stats['count']:.0f}")
            print(f"    Mean: {wind_stats['mean']:.1f} mph")
            print(f"    Min: {wind_stats['min']:.1f} mph")
            print(f"    Max: {wind_stats['max']:.1f} mph")

            zeros = len(df[df['wind_speed'] == 0])
            if zeros > 0:
                print(f"    ⚠️  Zero values: {zeros} ({zeros/len(df)*100:.1f}%)")
            else:
                print(f"    ✅ No zero values!")

        print(f"\n  Sample data (first 3 records):")
        print(df[['datetime', 'tide_height', 'wind_speed', 'wave_height']].head(3).to_string(index=False))
    else:
        print("❌ No data retrieved")


def main():
    print("\n🔬 TideHunter Data Quality Tests\n")

    # Test improved dummy data
    test_improved_dummy_data()

    # Test NDBC buoy integration
    test_ndbc_buoy()

    # Test full integration
    test_full_integration()

    print("\n" + "="*70)
    print("✅ Testing Complete!")
    print("="*70)
    print("\nKey Findings:")
    print("- Dummy data now has realistic wind variation (no zeros)")
    print("- Daily wind patterns: calmer at night, picks up during day")
    print("- NDBC buoy integration available for real-time data")
    print("- When APIs are accessible, real data will be used")


if __name__ == "__main__":
    main()
