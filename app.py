"""
TideHunter - Crabbing Forecast App
A Streamlit app for viewing hourly crabbing scores based on tide, wind, and wave conditions.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import os
from data_fetcher import WeatherDataFetcher
from crabbing_score import CrabbingScoreCalculator


# Page configuration
st.set_page_config(
    page_title="TideHunter - Crabbing Forecast",
    page_icon="🦀",
    layout="wide"
)

# Initialize session state for locations
if "locations" not in st.session_state:
    st.session_state.locations = {
        "San Francisco Bay": {"lat": 37.8063, "lon": -122.4659},
        "La Jolla, CA": {"lat": 32.8500, "lon": -117.2750},
    }

if "selected_location" not in st.session_state:
    st.session_state.selected_location = list(st.session_state.locations.keys())[0]

# Load locations from file if exists
LOCATIONS_FILE = "locations.json"


def load_locations():
    """Load locations from JSON file."""
    if os.path.exists(LOCATIONS_FILE):
        try:
            with open(LOCATIONS_FILE, "r") as f:
                st.session_state.locations = json.load(f)
        except Exception as e:
            st.error(f"Error loading locations: {e}")


def save_locations():
    """Save locations to JSON file."""
    try:
        with open(LOCATIONS_FILE, "w") as f:
            json.dump(st.session_state.locations, f, indent=2)
    except Exception as e:
        st.error(f"Error saving locations: {e}")


# Load locations on startup
load_locations()


def add_location(name: str, lat: float, lon: float):
    """Add a new location."""
    st.session_state.locations[name] = {"lat": lat, "lon": lon}
    save_locations()


def remove_location(name: str):
    """Remove a location."""
    if name in st.session_state.locations:
        del st.session_state.locations[name]
        save_locations()


def fetch_and_calculate_scores(location_name: str, days: int = 7) -> tuple[pd.DataFrame, dict]:
    """
    Fetch weather data and calculate crabbing scores.

    Args:
        location_name: Name of location
        days: Number of days to forecast

    Returns:
        Tuple of (DataFrame with scores, metadata dict)
    """
    if location_name not in st.session_state.locations:
        return pd.DataFrame(), {}

    location = st.session_state.locations[location_name]
    lat = location["lat"]
    lon = location["lon"]

    # Fetch data
    fetcher = WeatherDataFetcher()
    calculator = CrabbingScoreCalculator()

    start_date = datetime.now()
    end_date = start_date + timedelta(days=days)

    with st.spinner(f"Fetching data for {location_name}..."):
        df, metadata = fetcher.fetch_all_data(lat, lon, start_date, end_date)

    if df.empty:
        st.warning("No data available for this location.")
        return pd.DataFrame(), metadata

    # Calculate scores
    df_with_scores = calculator.calculate_dataframe_scores(df)

    return df_with_scores, metadata


def create_heatmap(df: pd.DataFrame):
    """
    Create a heatmap visualization of crabbing scores.

    Args:
        df: DataFrame with datetime and crabbing_score columns
    """
    if df.empty:
        st.warning("No data to display.")
        return

    # Prepare data for heatmap
    df_copy = df.copy()
    df_copy["date"] = pd.to_datetime(df_copy["datetime"]).dt.date
    df_copy["hour"] = pd.to_datetime(df_copy["datetime"]).dt.hour
    df_copy["day_name"] = pd.to_datetime(df_copy["datetime"]).dt.strftime("%A")

    # Pivot for heatmap
    heatmap_data = df_copy.pivot_table(
        values="crabbing_score",
        index="hour",
        columns="date",
        aggfunc="mean"
    )

    # Create heatmap with Plotly
    fig = go.Figure(data=go.Heatmap(
        z=heatmap_data.values,
        x=[col.strftime("%a %m/%d") for col in heatmap_data.columns],
        y=heatmap_data.index,
        colorscale=[
            [0, "rgb(165,0,38)"],
            [0.3, "rgb(244,109,67)"],
            [0.5, "rgb(253,174,97)"],
            [0.7, "rgb(171,221,164)"],
            [1, "rgb(0,104,55)"]
        ],
        colorbar=dict(title="Score"),
        hoverongaps=False,
        hovertemplate="Date: %{x}<br>Hour: %{y}:00<br>Score: %{z:.1f}<extra></extra>"
    ))

    fig.update_layout(
        title="Hourly Crabbing Scores - Week View",
        xaxis_title="Date",
        yaxis_title="Hour of Day",
        height=600,
        yaxis=dict(
            tickmode="linear",
            tick0=0,
            dtick=1
        )
    )

    st.plotly_chart(fig, use_container_width=True)


def create_conditions_chart(df: pd.DataFrame):
    """
    Create a line chart showing environmental conditions over time.

    Args:
        df: DataFrame with weather data
    """
    if df.empty:
        return

    fig = go.Figure()

    # Add traces for each condition
    fig.add_trace(go.Scatter(
        x=df["datetime"],
        y=df["tide_height"],
        name="Tide Height (ft)",
        yaxis="y1",
        line=dict(color="blue")
    ))

    fig.add_trace(go.Scatter(
        x=df["datetime"],
        y=df["wind_speed"],
        name="Wind Speed (mph)",
        yaxis="y2",
        line=dict(color="green")
    ))

    fig.add_trace(go.Scatter(
        x=df["datetime"],
        y=df["wave_height"],
        name="Wave Height (ft)",
        yaxis="y3",
        line=dict(color="red")
    ))

    fig.update_layout(
        title="Environmental Conditions",
        xaxis=dict(title="Date/Time"),
        yaxis=dict(
            title="Tide Height (ft)",
            titlefont=dict(color="blue"),
            tickfont=dict(color="blue")
        ),
        yaxis2=dict(
            title="Wind Speed (mph)",
            titlefont=dict(color="green"),
            tickfont=dict(color="green"),
            anchor="free",
            overlaying="y",
            side="left",
            position=0.05
        ),
        yaxis3=dict(
            title="Wave Height (ft)",
            titlefont=dict(color="red"),
            tickfont=dict(color="red"),
            anchor="x",
            overlaying="y",
            side="right"
        ),
        height=400,
        hovermode="x unified"
    )

    st.plotly_chart(fig, use_container_width=True)


def main():
    """Main application."""
    st.title("🦀 TideHunter - Crabbing Forecast")
    st.markdown("View hourly crabbing scores based on tide, wind, and wave conditions")

    # Sidebar for location management
    with st.sidebar:
        st.header("📍 Locations")

        # Select location
        if st.session_state.locations:
            location_names = list(st.session_state.locations.keys())
            selected = st.selectbox(
                "Select Location",
                location_names,
                index=location_names.index(st.session_state.selected_location) if st.session_state.selected_location in location_names else 0
            )
            st.session_state.selected_location = selected

            # Show coordinates
            loc = st.session_state.locations[selected]
            st.caption(f"Lat: {loc['lat']:.4f}, Lon: {loc['lon']:.4f}")

            # Remove location button
            if len(st.session_state.locations) > 1:
                if st.button("🗑️ Remove Location"):
                    remove_location(selected)
                    st.session_state.selected_location = list(st.session_state.locations.keys())[0]
                    st.rerun()

        st.divider()

        # Add new location
        st.subheader("➕ Add Location")
        with st.form("add_location_form"):
            new_name = st.text_input("Location Name", placeholder="e.g., Bodega Bay")
            col1, col2 = st.columns(2)
            with col1:
                new_lat = st.number_input("Latitude", value=37.8063, format="%.4f")
            with col2:
                new_lon = st.number_input("Longitude", value=-122.4659, format="%.4f")

            submit = st.form_submit_button("Add Location")
            if submit:
                if new_name and new_name not in st.session_state.locations:
                    add_location(new_name, new_lat, new_lon)
                    st.session_state.selected_location = new_name
                    st.success(f"Added {new_name}!")
                    st.rerun()
                elif new_name in st.session_state.locations:
                    st.error("Location already exists!")
                else:
                    st.error("Please enter a location name.")

        st.divider()

        # Forecast settings
        st.subheader("⚙️ Settings")
        forecast_days = st.slider("Forecast Days", 1, 14, 7)

    # Main content
    if not st.session_state.locations:
        st.warning("No locations available. Please add a location in the sidebar.")
        return

    # Fetch data button
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        if st.button("🔄 Fetch Latest Forecast", type="primary"):
            df_result, metadata = fetch_and_calculate_scores(
                st.session_state.selected_location,
                forecast_days
            )
            st.session_state.forecast_data = df_result
            st.session_state.data_metadata = metadata

    # Display forecast data
    if "forecast_data" not in st.session_state or st.session_state.forecast_data.empty:
        st.info("Click 'Fetch Latest Forecast' to load data.")
        # Auto-fetch on first load
        df_result, metadata = fetch_and_calculate_scores(
            st.session_state.selected_location,
            forecast_days
        )
        st.session_state.forecast_data = df_result
        st.session_state.data_metadata = metadata

    if "forecast_data" in st.session_state and not st.session_state.forecast_data.empty:
        df = st.session_state.forecast_data
        metadata = st.session_state.get("data_metadata", {})

        # Show data source warning if using simulated data
        if not metadata.get("using_real_data", False):
            st.error("""
⚠️ **WARNING: USING SIMULATED DATA - NOT SUITABLE FOR ACTUAL CRABBING TRIPS**

This app is running in an environment that blocks external API requests. The tide, wind, and wave data shown here is **simulated** and **NOT REAL**.

**DO NOT use this data for planning actual crabbing trips!**

**To get real data:**
1. Deploy this app to a server with internet access (Streamlit Cloud, Heroku, your local machine)
2. See `DEPLOYMENT.md` for complete instructions
3. All data sources are FREE and require no API keys

**Data sources when properly deployed:**
- Tides: NOAA CO-OPS API (official US government tide predictions)
- Wind: Open-Meteo API (global weather forecasts)
- Waves: Open-Meteo Marine API

See the README for verification steps to ensure you're getting real data.
            """)
        else:
            st.success(f"""
✅ **Using Real Data**
- Tides: {metadata.get('tide_source', 'Unknown')}
- Marine: {metadata.get('marine_source', 'Unknown')}
            """)

        # Current conditions
        st.header(f"📊 Forecast for {st.session_state.selected_location}")

        # Show current score
        current_row = df.iloc[0]
        current_score = current_row["crabbing_score"]
        calculator = CrabbingScoreCalculator()
        description = calculator.get_score_description(current_score)

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Current Score", f"{current_score}/10")
        with col2:
            st.metric("Tide Height", f"{current_row.get('tide_height', 0):.1f} ft")
        with col3:
            st.metric("Wind Speed", f"{current_row.get('wind_speed', 0):.1f} mph")
        with col4:
            st.metric("Wave Height", f"{current_row.get('wave_height', 0):.1f} ft")

        st.info(description)

        st.divider()

        # Heatmap
        st.subheader("🗓️ Week-by-Week Hourly Scores")
        create_heatmap(df)

        st.divider()

        # Conditions chart
        st.subheader("🌊 Environmental Conditions")
        create_conditions_chart(df)

        st.divider()

        # Detailed table
        st.subheader("📋 Detailed Hourly Forecast")

        # Format dataframe for display
        display_df = df.copy()
        display_df["datetime"] = pd.to_datetime(display_df["datetime"]).dt.strftime("%a %m/%d %I:%M %p")
        display_df = display_df[[
            "datetime",
            "crabbing_score",
            "tide_height",
            "wind_speed",
            "wave_height"
        ]].round(1)
        display_df.columns = ["Date/Time", "Score", "Tide (ft)", "Wind (mph)", "Waves (ft)"]

        # Color code scores
        def highlight_score(val):
            if pd.isna(val):
                return ""
            if val >= 8:
                color = "#00682d"
            elif val >= 7:
                color = "#76b82a"
            elif val >= 5:
                color = "#f9a825"
            elif val >= 4:
                color = "#f57c00"
            else:
                color = "#c62828"
            return f"background-color: {color}; color: white"

        styled_df = display_df.style.applymap(highlight_score, subset=["Score"])

        st.dataframe(styled_df, use_container_width=True, height=400)

    # Footer
    st.divider()
    st.caption("🦀 TideHunter - Data from NOAA and Open-Meteo")
    st.caption("⚠️ This is for informational purposes only. Always check local regulations and safety conditions.")


if __name__ == "__main__":
    main()
