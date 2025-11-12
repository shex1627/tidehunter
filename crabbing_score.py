"""
Crabbing score calculation module.
Calculates a score from 1-10 based on tide, wind, and wave conditions.
"""
import pandas as pd
import numpy as np
from typing import Tuple


class CrabbingScoreCalculator:
    """
    Calculates crabbing scores based on environmental conditions.

    Scoring factors:
    - Tide height: Lower tides often better for access (2-4 feet ideal)
    - Tide change: Moving tide is better (incoming/outgoing)
    - Wind speed: Lower is better (< 10 mph ideal, > 20 mph poor)
    - Wave height: Lower is better (< 2 feet ideal, > 4 feet poor)
    - Time of day: Dawn and dusk are prime times
    """

    def __init__(self):
        # Configuration for scoring
        self.ideal_tide_range = (2.0, 4.0)  # feet
        self.max_tide = 8.0
        self.ideal_wind_speed = 10.0  # mph
        self.max_wind_speed = 25.0  # mph
        self.ideal_wave_height = 2.0  # feet
        self.max_wave_height = 6.0  # feet
        self.prime_hours = [5, 6, 7, 17, 18, 19]  # Dawn and dusk hours

    def calculate_tide_score(self, tide_height: float, tide_change: float) -> float:
        """
        Calculate tide score (0-3 points).

        Args:
            tide_height: Tide height in feet
            tide_change: Rate of tide change (positive = rising, negative = falling)

        Returns:
            Score from 0 to 3
        """
        # Score based on tide height (0-2 points)
        if self.ideal_tide_range[0] <= tide_height <= self.ideal_tide_range[1]:
            height_score = 2.0
        elif tide_height < self.ideal_tide_range[0]:
            # Too low
            height_score = max(0, 2.0 * (tide_height / self.ideal_tide_range[0]))
        else:
            # Too high
            excess = tide_height - self.ideal_tide_range[1]
            max_excess = self.max_tide - self.ideal_tide_range[1]
            height_score = max(0, 2.0 * (1 - excess / max_excess))

        # Score based on tide movement (0-1 point)
        # Moving tide is good, slack tide is less ideal
        tide_movement = abs(tide_change)
        movement_score = min(1.0, tide_movement / 0.5)  # 0.5 ft/hr = full point

        return height_score + movement_score

    def calculate_wind_score(self, wind_speed: float) -> float:
        """
        Calculate wind score (0-3 points).

        Args:
            wind_speed: Wind speed in mph

        Returns:
            Score from 0 to 3
        """
        if wind_speed <= self.ideal_wind_speed:
            return 3.0
        elif wind_speed >= self.max_wind_speed:
            return 0.0
        else:
            # Linear decline from ideal to max
            return 3.0 * (1 - (wind_speed - self.ideal_wind_speed) / (self.max_wind_speed - self.ideal_wind_speed))

    def calculate_wave_score(self, wave_height: float) -> float:
        """
        Calculate wave score (0-3 points).

        Args:
            wave_height: Wave height in feet

        Returns:
            Score from 0 to 3
        """
        if wave_height <= self.ideal_wave_height:
            return 3.0
        elif wave_height >= self.max_wave_height:
            return 0.0
        else:
            # Linear decline from ideal to max
            return 3.0 * (1 - (wave_height - self.ideal_wave_height) / (self.max_wave_height - self.ideal_wave_height))

    def calculate_time_bonus(self, hour: int) -> float:
        """
        Calculate time of day bonus (0-1 point).

        Args:
            hour: Hour of day (0-23)

        Returns:
            Bonus from 0 to 1
        """
        if hour in self.prime_hours:
            return 1.0
        else:
            return 0.0

    def calculate_score(
        self,
        tide_height: float,
        tide_change: float,
        wind_speed: float,
        wave_height: float,
        hour: int
    ) -> Tuple[float, dict]:
        """
        Calculate overall crabbing score.

        Args:
            tide_height: Tide height in feet
            tide_change: Tide change rate in feet/hour
            wind_speed: Wind speed in mph
            wave_height: Wave height in feet
            hour: Hour of day (0-23)

        Returns:
            Tuple of (overall_score, breakdown_dict)
        """
        tide_score = self.calculate_tide_score(tide_height, tide_change)
        wind_score = self.calculate_wind_score(wind_speed)
        wave_score = self.calculate_wave_score(wave_height)
        time_bonus = self.calculate_time_bonus(hour)

        # Total score out of 10
        raw_score = tide_score + wind_score + wave_score + time_bonus
        final_score = min(10.0, max(1.0, raw_score))  # Clamp between 1 and 10

        breakdown = {
            "tide_score": round(tide_score, 2),
            "wind_score": round(wind_score, 2),
            "wave_score": round(wave_score, 2),
            "time_bonus": round(time_bonus, 2),
            "total": round(final_score, 1)
        }

        return round(final_score, 1), breakdown

    def calculate_dataframe_scores(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate crabbing scores for entire dataframe.

        Args:
            df: DataFrame with columns: datetime, tide_height, wave_height, wind_speed

        Returns:
            DataFrame with added score column
        """
        if df.empty:
            return df

        # Calculate tide change (rate)
        df = df.copy()
        df["tide_change"] = df["tide_height"].diff().fillna(0)

        # Extract hour
        df["hour"] = pd.to_datetime(df["datetime"]).dt.hour

        # Calculate scores
        scores = []
        for _, row in df.iterrows():
            score, _ = self.calculate_score(
                tide_height=row.get("tide_height", 3.0),
                tide_change=row.get("tide_change", 0.0),
                wind_speed=row.get("wind_speed", 10.0),
                wave_height=row.get("wave_height", 2.0),
                hour=row.get("hour", 12)
            )
            scores.append(score)

        df["crabbing_score"] = scores
        return df

    def get_score_description(self, score: float) -> str:
        """
        Get text description of crabbing conditions.

        Args:
            score: Crabbing score (1-10)

        Returns:
            Description string
        """
        if score >= 8.5:
            return "🦀 Excellent - Prime crabbing conditions!"
        elif score >= 7.0:
            return "✅ Very Good - Great time to go crabbing"
        elif score >= 5.5:
            return "👍 Good - Decent conditions for crabbing"
        elif score >= 4.0:
            return "⚠️ Fair - Challenging but possible"
        else:
            return "❌ Poor - Not recommended for crabbing"
