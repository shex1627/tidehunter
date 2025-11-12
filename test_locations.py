"""
Test script for Pacifica Municipal Pier and Baker Beach crabbing scores.
"""
from datetime import datetime, timedelta
from data_fetcher import WeatherDataFetcher
from crabbing_score import CrabbingScoreCalculator
import pandas as pd


def test_location(name, lat, lon, days=7):
    """Test a specific location and display results."""
    print(f"\n{'='*70}")
    print(f"🦀 {name}")
    print(f"📍 Coordinates: {lat:.4f}, {lon:.4f}")
    print('='*70)

    fetcher = WeatherDataFetcher()
    calculator = CrabbingScoreCalculator()

    start_date = datetime.now()
    end_date = start_date + timedelta(days=days)

    # Fetch data
    print(f"\n⏳ Fetching {days}-day forecast...")
    df = fetcher.fetch_all_data(lat, lon, start_date, end_date)

    if df.empty:
        print("❌ No data available")
        return None

    # Calculate scores
    df_with_scores = calculator.calculate_dataframe_scores(df)

    # Display statistics
    print(f"\n📊 Score Statistics:")
    print(f"   Total hours analyzed: {len(df_with_scores)}")
    print(f"   Score range: {df_with_scores['crabbing_score'].min():.1f} - {df_with_scores['crabbing_score'].max():.1f}")
    print(f"   Average score: {df_with_scores['crabbing_score'].mean():.1f}")
    print(f"   Excellent (8.5+): {len(df_with_scores[df_with_scores['crabbing_score'] >= 8.5])} hours")
    print(f"   Very Good (7.0+): {len(df_with_scores[df_with_scores['crabbing_score'] >= 7.0])} hours")
    print(f"   Good (5.5+): {len(df_with_scores[df_with_scores['crabbing_score'] >= 5.5])} hours")

    # Show current conditions
    current = df_with_scores.iloc[0]
    print(f"\n🌊 Current Conditions:")
    print(f"   Score: {current['crabbing_score']:.1f}/10.0")
    print(f"   {calculator.get_score_description(current['crabbing_score'])}")
    print(f"   Tide: {current['tide_height']:.1f} ft")
    print(f"   Wind: {current['wind_speed']:.1f} mph")
    print(f"   Waves: {current['wave_height']:.1f} ft")

    # Show top 5 times
    print(f"\n⭐ Top 5 Crabbing Times:")
    top_times = df_with_scores.nlargest(5, 'crabbing_score')
    for i, (idx, row) in enumerate(top_times.iterrows(), 1):
        dt = pd.to_datetime(row['datetime'])
        day_str = dt.strftime("%a %m/%d")
        time_str = dt.strftime("%I:%M %p")
        score = row['crabbing_score']
        tide = row['tide_height']
        wind = row['wind_speed']
        waves = row['wave_height']

        # Get emoji based on score
        if score >= 8.5:
            emoji = "🦀"
        elif score >= 7.0:
            emoji = "✅"
        elif score >= 5.5:
            emoji = "👍"
        else:
            emoji = "⚠️"

        print(f"   {i}. {emoji} {day_str} at {time_str} - Score: {score:.1f}/10")
        print(f"      Tide: {tide:.1f}ft, Wind: {wind:.1f}mph, Waves: {waves:.1f}ft")

    # Show today's hourly forecast
    print(f"\n📅 Today's Hourly Forecast:")
    today = df_with_scores[pd.to_datetime(df_with_scores['datetime']).dt.date == start_date.date()]

    if len(today) > 0:
        for idx, row in today.head(12).iterrows():  # Show next 12 hours
            dt = pd.to_datetime(row['datetime'])
            time_str = dt.strftime("%I:%M %p")
            score = row['crabbing_score']

            # Visual bar
            bar_length = int(score)
            bar = "█" * bar_length + "░" * (10 - bar_length)

            print(f"   {time_str:>8} │ {bar} {score:.1f}")

    return df_with_scores


def main():
    """Test both locations."""
    print("\n" + "="*70)
    print("🦀 TIDEHUNTER - LOCATION TESTING")
    print("="*70)

    # Location coordinates
    locations = {
        "Pacifica Municipal Pier": {
            "lat": 37.6138,
            "lon": -122.4872
        },
        "Baker Beach, San Francisco": {
            "lat": 37.7933,
            "lon": -122.4834
        }
    }

    results = {}

    # Test each location
    for name, coords in locations.items():
        results[name] = test_location(name, coords["lat"], coords["lon"], days=7)

    # Compare locations
    print(f"\n{'='*70}")
    print("📊 LOCATION COMPARISON")
    print('='*70)

    for name, df in results.items():
        if df is not None:
            avg_score = df['crabbing_score'].mean()
            max_score = df['crabbing_score'].max()
            excellent_hours = len(df[df['crabbing_score'] >= 8.5])

            print(f"\n{name}:")
            print(f"   Average Score: {avg_score:.1f}/10.0")
            print(f"   Peak Score: {max_score:.1f}/10.0")
            print(f"   Excellent Hours: {excellent_hours}")

    print(f"\n{'='*70}")
    print("✅ Testing complete!")
    print('='*70)
    print("\nTip: Add these locations to your app using the sidebar!")
    print("Run the app with: streamlit run app.py")


if __name__ == "__main__":
    main()
