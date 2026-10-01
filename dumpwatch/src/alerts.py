import os
import sys
from datetime import datetime, timedelta
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


def generate_alerts(reports_df: pd.DataFrame, hotspots_summary: pd.DataFrame, risk_df: pd.DataFrame) -> list:
    """Generate high-priority operational alerts based on defined business rules."""
    alerts = []
    now = datetime.now()

    if reports_df.empty:
        return alerts

    df = reports_df.copy()
    df["timestamp_dt"] = pd.to_datetime(df["timestamp"], errors="coerce")

    # Rule (a): Severity >= 4 in last 24h
    cutoff_24h = now - timedelta(hours=24)
    recent_high_sev = df[(df["severity"] >= 4) & (df["timestamp_dt"] >= cutoff_24h)]
    for _, row in recent_high_sev.iterrows():
        loc_str = row.get("location_text", "Thane")
        alerts.append({
            "level": "High",
            "title": f"High Severity Incident ({row['severity']}/5)",
            "message": f"Critical complaint reported: '{str(row['raw_text'])[:80]}...' ({row['waste_type']})",
            "location": str(loc_str),
            "time": str(row["timestamp"]),
        })

    # Rule (d): Medical or Industrial waste anywhere in recent reports
    hazardous = df[df["waste_type"].isin(["medical waste", "industrial waste"])]
    for _, row in hazardous.head(10).iterrows():
        alerts.append({
            "level": "Critical",
            "title": f"Hazardous Material Detected ({str(row['waste_type']).title()})",
            "message": f"Immediate containment needed for {row['waste_type']} near {row.get('location_text', 'Thane')}.",
            "location": str(row.get("location_text", "Thane")),
            "time": str(row["timestamp"]),
        })

    # Rule (c): Any Critical risk grid cell
    if not risk_df.empty and "risk_level" in risk_df.columns:
        critical_cells = risk_df[risk_df["risk_level"] == "Critical"]
        for _, cell in critical_cells.iterrows():
            alerts.append({
                "level": "Critical",
                "title": f"Critical Risk Zone (Score: {cell['risk_score']})",
                "message": f"Grid cell around [{cell['center_lat']}, {cell['center_lon']}] predicted to have severe dumping surge next week.",
                "location": f"Grid {cell['cell_id']}",
                "time": now.strftime("%Y-%m-%d %H:%M:%S"),
            })

    # Rule (b): Hotspot spike (last 7 days count >= 1.5x previous week)
    if not hotspots_summary.empty and "cluster_id" in df.columns:
        cutoff_7d = now - timedelta(days=7)
        cutoff_14d = now - timedelta(days=14)
        for _, hs in hotspots_summary.iterrows():
            cid = hs["cluster_id"]
            cluster_reports = df[df["cluster_id"] == cid]
            c_7d = len(cluster_reports[cluster_reports["timestamp_dt"] >= cutoff_7d])
            c_prev_7d = len(cluster_reports[(cluster_reports["timestamp_dt"] >= cutoff_14d) & (cluster_reports["timestamp_dt"] < cutoff_7d)])

            if c_7d >= 4 and (c_prev_7d == 0 or (c_7d / max(c_prev_7d, 1)) >= 1.5):
                alerts.append({
                    "level": "High",
                    "title": f"Hotspot Incident Spike (Cluster #{cid})",
                    "message": f"Dumping incidents surged by {c_7d} reports in last 7 days near {hs['nearest_locality']}.",
                    "location": str(hs["nearest_locality"]),
                    "time": now.strftime("%Y-%m-%d %H:%M:%S"),
                })

    # Remove exact duplicate alerts
    unique_alerts = []
    seen = set()
    for a in alerts:
        key = (a["title"], a["location"])
        if key not in seen:
            seen.add(key)
            unique_alerts.append(a)

    return unique_alerts
