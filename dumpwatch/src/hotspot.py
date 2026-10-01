import math
import os
import sys
import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


def get_nearest_locality(lat, lon):
    min_dist = float("inf")
    nearest = "Thane"
    for loc_name, coords in config.THANE_LOCALITIES.items():
        d = math.hypot(lat - coords["lat"], lon - coords["lon"])
        if d < min_dist:
            min_dist = d
            nearest = loc_name
    return nearest


def find_hotspots(reports_df: pd.DataFrame):
    """Find hotspot clusters using DBSCAN with haversine metric (~400m eps)."""
    if reports_df.empty:
        empty_summary = pd.DataFrame(columns=["cluster_id", "center_lat", "center_lon", "incident_count", "avg_severity", "dominant_waste_type", "nearest_locality"])
        return reports_df.assign(cluster_id=-1), empty_summary

    df = reports_df.copy()
    valid_df = df[df["status"] != "Duplicate"].copy() if "status" in df.columns else df.copy()

    if valid_df.empty or len(valid_df) < 4:
        df["cluster_id"] = -1
        empty_summary = pd.DataFrame(columns=["cluster_id", "center_lat", "center_lon", "incident_count", "avg_severity", "dominant_waste_type", "nearest_locality"])
        return df, empty_summary

    # Extract coordinates in radians for haversine
    coords = valid_df[["lat", "lon"]].values if "lat" in valid_df.columns else np.array([r for r in valid_df["coordinates"]])
    coords_rad = np.radians(coords)

    # 400m in earth radius radians (~6371km)
    kms_per_radian = 6371.0
    epsilon = 0.400 / kms_per_radian

    db = DBSCAN(eps=epsilon, min_samples=4, metric="haversine").fit(coords_rad)
    valid_df["cluster_id"] = db.labels_

    # Map back to main df
    df["cluster_id"] = -1
    df.loc[valid_df.index, "cluster_id"] = valid_df["cluster_id"]

    summary_rows = []
    clusters = valid_df[valid_df["cluster_id"] != -1].groupby("cluster_id")

    for cid, group in clusters:
        c_lat = round(float(group["lat"].mean() if "lat" in group else np.mean([c[0] for c in group["coordinates"]])), 5)
        c_lon = round(float(group["lon"].mean() if "lon" in group else np.mean([c[1] for c in group["coordinates"]])), 5)
        count = len(group)
        avg_sev = round(float(group["severity"].mean()), 2)
        dom_waste = group["waste_type"].mode()[0] if not group["waste_type"].empty else "household garbage"
        locality = get_nearest_locality(c_lat, c_lon)

        summary_rows.append({
            "cluster_id": int(cid),
            "center_lat": c_lat,
            "center_lon": c_lon,
            "incident_count": count,
            "avg_severity": avg_sev,
            "dominant_waste_type": dom_waste,
            "nearest_locality": locality,
        })

    summary_df = pd.DataFrame(summary_rows)
    return df, summary_df
