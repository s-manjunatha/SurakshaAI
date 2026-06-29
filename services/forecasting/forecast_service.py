"""Crime forecasting using Prophet and sklearn."""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Optional
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder


class ForecastService:
    def forecast_crime_volume(self, daily_counts: List[dict], periods: int = 30) -> List[dict]:
        """Forecast crime volume using Prophet if available, else simple moving average."""
        if not daily_counts:
            return []

        df = pd.DataFrame(daily_counts)
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date")

        try:
            from prophet import Prophet
            prophet_df = df.rename(columns={"date": "ds", "count": "y"})
            model = Prophet(yearly_seasonality=True, weekly_seasonality=True, daily_seasonality=False)
            model.fit(prophet_df)
            future = model.make_future_dataframe(periods=periods)
            forecast = model.predict(future)
            future_forecast = forecast.tail(periods)
            return [
                {
                    "date": row["ds"].strftime("%Y-%m-%d"),
                    "predicted_count": round(max(0, row["yhat"]), 1),
                    "lower_bound": round(max(0, row["yhat_lower"]), 1),
                    "upper_bound": round(max(0, row["yhat_upper"]), 1),
                }
                for _, row in future_forecast.iterrows()
            ]
        except Exception:
            return self._simple_forecast(df, periods)

    def _simple_forecast(self, df: pd.DataFrame, periods: int) -> List[dict]:
        avg = df["count"].tail(30).mean() if len(df) >= 30 else df["count"].mean()
        std = df["count"].tail(30).std() if len(df) >= 30 else df["count"].std()
        if pd.isna(std):
            std = avg * 0.2
        last_date = df["date"].max()
        results = []
        for i in range(1, periods + 1):
            d = last_date + timedelta(days=i)
            seasonal = avg * (1 + 0.1 * np.sin(2 * np.pi * i / 7))
            results.append({
                "date": d.strftime("%Y-%m-%d"),
                "predicted_count": round(max(0, seasonal), 1),
                "lower_bound": round(max(0, seasonal - std), 1),
                "upper_bound": round(seasonal + std, 1),
            })
        return results

    def predict_hotspots(self, location_data: List[dict], top_n: int = 10) -> List[dict]:
        """Predict future hotspots based on recent trends."""
        if not location_data:
            return []

        df = pd.DataFrame(location_data)
        grouped = df.groupby(["district", "latitude", "longitude"]).agg(
            recent_count=("count", "sum"),
            avg_count=("count", "mean"),
        ).reset_index()

        grouped["risk_score"] = (
            grouped["recent_count"] * 0.6 + grouped["avg_count"] * 0.4
        )
        grouped = grouped.sort_values("risk_score", ascending=False).head(top_n)

        return [
            {
                "latitude": float(row["latitude"]),
                "longitude": float(row["longitude"]),
                "district": row["district"],
                "predicted_intensity": round(float(row["risk_score"]), 2),
                "risk_level": "high" if row["risk_score"] > grouped["risk_score"].median() else "medium",
            }
            for _, row in grouped.iterrows()
        ]

    def region_risk_scores(self, district_stats: List[dict]) -> List[dict]:
        """Calculate risk scores by region."""
        if not district_stats:
            return []

        results = []
        for stat in district_stats:
            count = stat.get("crime_count", 0)
            prev_count = stat.get("prev_count", count)
            growth = ((count - prev_count) / max(prev_count, 1)) * 100
            risk = min(100, count * 0.01 + abs(growth) * 0.5)
            trend = "increasing" if growth > 5 else "decreasing" if growth < -5 else "stable"
            results.append({
                "district": stat["district"],
                "risk_score": round(risk, 1),
                "crime_count": count,
                "trend": trend,
            })
        return sorted(results, key=lambda x: x["risk_score"], reverse=True)


forecast_service = ForecastService()
