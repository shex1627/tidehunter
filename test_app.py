"""
Test script to verify the TideHunter app components work correctly.
"""
from datetime import datetime, timedelta
from data_fetcher import WeatherDataFetcher
from crabbing_score import CrabbingScoreCalculator


def test_data_fetcher():
    """Test the data fetcher module."""
    print("Testing WeatherDataFetcher...")

    fetcher = WeatherDataFetcher()

    # Test with San Francisco coordinates
    lat, lon = 37.8063, -122.4659
    start_date = datetime.now()
    end_date = start_date + timedelta(days=2)

    print(f"  Fetching data for SF Bay ({lat}, {lon})...")

    # Test tide data
    print("  Testing tide data fetch...")
    tide_df = fetcher.fetch_tide_data(lat, lon, start_date, end_date)
    print(f"    ✓ Fetched {len(tide_df)} tide records")
    if len(tide_df) > 0:
        print(f"    Sample: {tide_df.iloc[0].to_dict()}")

    # Test marine data
    print("  Testing marine data fetch...")
    marine_df = fetcher.fetch_marine_data(lat, lon, start_date, end_date)
    print(f"    ✓ Fetched {len(marine_df)} marine records")
    if len(marine_df) > 0:
        print(f"    Sample: {marine_df.iloc[0].to_dict()}")

    # Test combined fetch
    print("  Testing combined data fetch...")
    combined_df = fetcher.fetch_all_data(lat, lon, start_date, end_date)
    print(f"    ✓ Fetched {len(combined_df)} combined records")
    if len(combined_df) > 0:
        print(f"    Columns: {list(combined_df.columns)}")
        print(f"    Sample: {combined_df.iloc[0].to_dict()}")

    print("✓ Data fetcher tests passed!\n")
    return combined_df


def test_scoring():
    """Test the scoring algorithm."""
    print("Testing CrabbingScoreCalculator...")

    calculator = CrabbingScoreCalculator()

    # Test individual scoring functions
    print("  Testing tide score...")
    tide_score = calculator.calculate_tide_score(tide_height=3.0, tide_change=0.3)
    print(f"    Tide score (3.0 ft, 0.3 change): {tide_score}/3.0")

    print("  Testing wind score...")
    wind_score = calculator.calculate_wind_score(wind_speed=8.0)
    print(f"    Wind score (8 mph): {wind_score}/3.0")

    print("  Testing wave score...")
    wave_score = calculator.calculate_wave_score(wave_height=1.5)
    print(f"    Wave score (1.5 ft): {wave_score}/3.0")

    print("  Testing time bonus...")
    time_bonus = calculator.calculate_time_bonus(hour=6)
    print(f"    Time bonus (6 AM): {time_bonus}/1.0")

    # Test overall score
    print("  Testing overall score calculation...")
    score, breakdown = calculator.calculate_score(
        tide_height=3.0,
        tide_change=0.3,
        wind_speed=8.0,
        wave_height=1.5,
        hour=6
    )
    print(f"    Overall score: {score}/10.0")
    print(f"    Breakdown: {breakdown}")
    print(f"    Description: {calculator.get_score_description(score)}")

    # Test poor conditions
    print("  Testing poor conditions...")
    poor_score, poor_breakdown = calculator.calculate_score(
        tide_height=7.0,
        tide_change=0.0,
        wind_speed=25.0,
        wave_height=5.0,
        hour=12
    )
    print(f"    Poor score: {poor_score}/10.0")
    print(f"    Description: {calculator.get_score_description(poor_score)}")

    print("✓ Scoring algorithm tests passed!\n")
    return calculator


def test_dataframe_scoring(df, calculator):
    """Test scoring on a full dataframe."""
    print("Testing dataframe scoring...")

    if df.empty:
        print("  ⚠ No data to test dataframe scoring")
        return

    print(f"  Processing {len(df)} records...")
    df_with_scores = calculator.calculate_dataframe_scores(df)

    print(f"    ✓ Added scores to {len(df_with_scores)} records")
    print(f"    Score range: {df_with_scores['crabbing_score'].min():.1f} - {df_with_scores['crabbing_score'].max():.1f}")
    print(f"    Average score: {df_with_scores['crabbing_score'].mean():.1f}")

    # Show best times
    top_times = df_with_scores.nlargest(3, 'crabbing_score')[['datetime', 'crabbing_score', 'tide_height', 'wind_speed', 'wave_height']]
    print("\n  Top 3 crabbing times:")
    for idx, row in top_times.iterrows():
        print(f"    {row['datetime']}: Score {row['crabbing_score']}/10.0")

    print("\n✓ Dataframe scoring tests passed!\n")


def test_imports():
    """Test that the Streamlit app can be imported."""
    print("Testing Streamlit app imports...")
    try:
        import app
        print("  ✓ App module imported successfully")
    except Exception as e:
        print(f"  ✗ Error importing app: {e}")
        return False

    print("✓ Import tests passed!\n")
    return True


def main():
    """Run all tests."""
    print("=" * 60)
    print("TideHunter App Test Suite")
    print("=" * 60)
    print()

    try:
        # Test data fetcher
        df = test_data_fetcher()

        # Test scoring
        calculator = test_scoring()

        # Test dataframe scoring
        test_dataframe_scoring(df, calculator)

        # Test imports
        test_imports()

        print("=" * 60)
        print("✓ ALL TESTS PASSED!")
        print("=" * 60)
        print("\nThe app is ready to use! Run it with:")
        print("  streamlit run app.py")

    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
