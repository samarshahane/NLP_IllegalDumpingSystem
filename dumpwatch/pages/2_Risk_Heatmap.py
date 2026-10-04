import os
import sys
import folium
from folium.plugins import HeatMap
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from src.hotspot import find_hotspots
from src.risk import predict_risk
from src.storage import Storage, get_reports_df

st.set_page_config(page_title="Risk Heatmap - DumpWatch Enterprise", layout="wide")

# Check Auth
if not st.session_state.get("authenticated", False):
    st.warning("Restricted Page: Backoffice / Admin authentication required. Please log in from the main portal.")
    st.stop()

st.title("Predicted Risk Heatmap & Hotspot Analysis")

df = get_reports_df()

if df.empty:
    st.info("No reports data available.")
    st.stop()

storage = Storage()
reports_data = storage.get_all()

risk_df, heat_points, mae = predict_risk(reports_data)
_, hotspots_summary = find_hotspots(df)

m = folium.Map(location=config.DEFAULT_MAP_CENTER, zoom_start=config.DEFAULT_ZOOM)

if heat_points:
    HeatMap(heat_points, radius=20, blur=15, max_zoom=13).add_to(m)

if not hotspots_summary.empty:
    for _, hs in hotspots_summary.iterrows():
        folium.Circle(
            location=[hs["center_lat"], hs["center_lon"]],
            radius=400,
            color="red",
            fill=True,
            fill_color="red",
            fill_opacity=0.2,
            popup=f"<b>Hotspot #{hs['cluster_id']}</b><br>Locality: {hs['nearest_locality']}<br>Incidents: {hs['incident_count']}<br>Avg Severity: {hs['avg_severity']}",
        ).add_to(m)

st_folium(m, width=1100, height=500)

st.divider()

col1, col2 = st.columns([2, 1])
with col1:
    st.subheader("Top High-Risk Grid Zones")
    if not risk_df.empty:
        top_risk = risk_df.sort_values("risk_score", ascending=False).head(10)
        display_df = top_risk[["cell_id", "center_lat", "center_lon", "risk_score", "risk_level", "pred_count"]]
        st.dataframe(display_df, use_container_width=True)
    else:
        st.info("Insufficient data to compute grid risk zones.")

with col2:
    st.subheader("Model Validation")
    st.metric("RandomForest Model MAE", f"{mae} incidents/week")
    st.caption("RandomForestRegressor evaluated via time-based split across 500m spatial grid cells.")

