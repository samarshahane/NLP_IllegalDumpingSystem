import os
import sys
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error
import streamlit as st

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


def assign_grid_cell(lat, lon, grid_size_deg=0.0045):
    """Assign lat/lon to ~500m grid cell ID."""
    lat_idx = int(np.floor(lat / grid_size_deg))
    lon_idx = int(np.floor(lon / grid_size_deg))
    cell_id = f"CELL_{lat_idx}_{lon_idx}"
    center_lat = round((lat_idx + 0.5) * grid_size_deg, 5)
    center_lon = round((lon_idx + 0.5) * grid_size_deg, 5)
    return cell_id, center_lat, center_lon


@st.cache_resource
def train_risk_model(reports_df_hash: str, reports_data: list):
    """Train RandomForestRegressor on weekly grid aggregations."""
    if not reports_data:
        return None, 0.0, pd.DataFrame()

    df = pd.DataFrame(reports_data)
    if df.empty or "timestamp" not in df.columns:
        return None, 0.0, pd.DataFrame()

    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["week"] = df["timestamp"].dt.to_period("W").dt.to_timestamp()

    # Assign cells
    cells, center_lats, center_lons = [], [], []
    for _, row in df.iterrows():
        lat = row["lat"] if "lat" in row and pd.notnull(row["lat"]) else row["coordinates"][0]
        lon = row["lon"] if "lon" in row and pd.notnull(row["lon"]) else row["coordinates"][1]
        cid, clat, clon = assign_grid_cell(lat, lon)
        cells.append(cid)
        center_lats.append(clat)
        center_lons.append(clon)

    df["cell_id"] = cells
    df["center_lat"] = center_lats
    df["center_lon"] = center_lons

    # Weekly aggregation per cell
    weekly = df.groupby(["cell_id", "week", "center_lat", "center_lon"]).agg(
        incident_count=("report_id", "count"),
        avg_severity=("severity", "mean"),
    ).reset_index()

    # Lag features
    weekly = weekly.sort_values(["cell_id", "week"])
    weekly["prev_1w"] = weekly.groupby("cell_id")["incident_count"].shift(1).fillna(0)
    weekly["prev_2w"] = weekly.groupby("cell_id")["incident_count"].shift(2).fillna(0)
    weekly["roll_4w"] = weekly.groupby("cell_id")["incident_count"].transform(lambda x: x.rolling(4, min_periods=1).mean()).fillna(0)

    feature_cols = ["prev_1w", "prev_2w", "roll_4w", "avg_severity"]
    X = weekly[feature_cols]
    y = weekly["incident_count"]

    if len(X) < 10:
        return None, 0.0, weekly

    # Time-based split (no shuffle)
    split_idx = int(len(X) * 0.8)
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

    model = RandomForestRegressor(n_estimators=50, max_depth=6, random_state=42)
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    mae = round(float(mean_absolute_error(y_test, preds)), 3)

    return model, mae, weekly


def predict_risk(reports_data: list):
    """Predict risk per grid cell and return risk levels and folium heatmap points."""
    if not reports_data:
        return pd.DataFrame(), [], 0.0

    df_hash = str(len(reports_data))
    model, mae, weekly = train_risk_model(df_hash, reports_data)

    if weekly.empty:
        return pd.DataFrame(), [], 0.0

    latest_cells = weekly.groupby("cell_id").last().reset_index()

    if model is not None:
        feature_cols = ["prev_1w", "prev_2w", "roll_4w", "avg_severity"]
        X_latest = latest_cells[feature_cols].fillna(0)
        predicted_counts = model.predict(X_latest)
    else:
        predicted_counts = latest_cells["incident_count"].values

    latest_cells["pred_count"] = predicted_counts
    max_pred = max(latest_cells["pred_count"].max(), 1.0)

    # Risk score 0-100
    latest_cells["risk_score"] = (latest_cells["pred_count"] / max_pred * 100).round(1)

    def get_risk_level(score):
        if score >= 75:
            return "Critical"
        elif score >= 50:
            return "High"
        elif score >= 25:
            return "Medium"
        return "Low"

    latest_cells["risk_level"] = latest_cells["risk_score"].apply(get_risk_level)

    heatmap_points = []
    for _, row in latest_cells.iterrows():
        weight = float(row["risk_score"] / 100.0)
        heatmap_points.append([row["center_lat"], row["center_lon"], weight])

    return latest_cells, heatmap_points, mae
