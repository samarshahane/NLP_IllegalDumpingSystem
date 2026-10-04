import os
import sys
import folium
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from src.storage import Storage, get_reports_df, get_waste_types

st.set_page_config(page_title="Live Map - DumpWatch Enterprise", layout="wide")

# Check Auth
if not st.session_state.get("authenticated", False):
    st.warning("Restricted Page: Backoffice / Admin authentication required. Please log in from the main portal.")
    st.stop()

st.title("Live Incidents Map")

df = get_reports_df()

if df.empty:
    st.info("No incident records available.")
    st.stop()

# Sidebar Filters
st.sidebar.header("Filter Incident Reports")
all_statuses = ["Pending", "Resolved", "Duplicate", "Rejected"]
selected_statuses = st.sidebar.multiselect("Status Filter", options=all_statuses, default=["Pending", "Resolved"])

available_wastes = get_waste_types()
selected_wastes = st.sidebar.multiselect("Waste Type", options=available_wastes, default=[])

available_sources = list(df["source"].unique()) if "source" in df.columns else []
selected_sources = st.sidebar.multiselect("Source Feed", options=available_sources, default=[])

filtered_df = df.copy()

if selected_statuses:
    filtered_df = filtered_df[filtered_df["status"].isin(selected_statuses)]
if selected_wastes:
    filtered_df = filtered_df[filtered_df["waste_type"].isin(selected_wastes)]
if selected_sources:
    filtered_df = filtered_df[filtered_df["source"].isin(selected_sources)]

m = folium.Map(location=config.DEFAULT_MAP_CENTER, zoom_start=config.DEFAULT_ZOOM)

status_colors = {
    "Pending": "orange",
    "Resolved": "green",
    "Duplicate": "blue",
    "Rejected": "gray",
}

for _, row in filtered_df.iterrows():
    lat = row.get("lat", config.DEFAULT_MAP_CENTER[0])
    lon = row.get("lon", config.DEFAULT_MAP_CENTER[1])
    color = status_colors.get(row.get("status"), "orange")

    img_html = ""
    if pd.notnull(row.get("image_path")) and row.get("image_path") and os.path.exists(str(row.get("image_path"))):
        img_html = f"<br><img src='file:///{row['image_path']}' width='150'>"

    popup_content = f"""
    <b>ID:</b> {row['report_id']}<br>
    <b>Status:</b> {row['status']}<br>
    <b>Waste Type:</b> {row['waste_type']}<br>
    <b>Severity:</b> {row['severity']}/5<br>
    <b>Time:</b> {row['timestamp']}<br>
    <b>Summary:</b> {row['raw_text'][:100]}...{img_html}
    """

    folium.CircleMarker(
        location=[lat, lon],
        radius=6,
        color=color,
        fill=True,
        fill_color=color,
        fill_opacity=0.7,
        popup=folium.Popup(popup_content, max_width=300),
    ).add_to(m)

st_folium(m, width=1100, height=500)

st.divider()

st.subheader("Update Complaint Status")
pending_df = df[df["status"] == "Pending"] if not df.empty else pd.DataFrame()
if not pending_df.empty:
    target_id = st.selectbox("Select Pending Report ID:", pending_df["report_id"].unique())
    if st.button("Mark as Resolved", type="primary"):
        storage = Storage()
        storage.update_status(target_id, "Resolved")
        st.success(f"Report {target_id} updated to Resolved.")
        st.rerun()
else:
    st.info("No pending complaints available for resolution.")

