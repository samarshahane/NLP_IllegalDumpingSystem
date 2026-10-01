import os
import sys
import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.storage import get_reports_df

st.set_page_config(page_title="Analytics - DumpWatch", page_icon="📊", layout="wide")
st.title("📊 Dumping Insights & Analytics Dashboard")

df = get_reports_df()

if df.empty:
    st.info("No reports yet.")
    st.stop()

df["timestamp_dt"] = pd.to_datetime(df["timestamp"], errors="coerce")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Incidents Trend Over Time")
    weekly_df = df.set_index("timestamp_dt").resample("W")["report_id"].count().reset_index()
    fig1 = px.line(weekly_df, x="timestamp_dt", y="report_id", labels={"timestamp_dt": "Date", "report_id": "Incidents"})
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    st.subheader("Waste Type Distribution (Inc. Custom Types)")
    waste_counts = df["waste_type"].value_counts().reset_index()
    fig2 = px.pie(waste_counts, names="waste_type", values="count", hole=0.4)
    st.plotly_chart(fig2, use_container_width=True)

st.divider()

col3, col4 = st.columns(2)

with col3:
    st.subheader("Reports by Source Feed")
    source_counts = df["source"].value_counts().reset_index()
    fig3 = px.bar(source_counts, x="source", y="count", color="source")
    st.plotly_chart(fig3, use_container_width=True)

with col4:
    st.subheader("Severity Distribution")
    fig4 = px.histogram(df, x="severity", nbins=5, color_discrete_sequence=["#EBCB8B"])
    st.plotly_chart(fig4, use_container_width=True)

st.divider()

col5, col6 = st.columns(2)

with col5:
    st.subheader("Top 10 Incident Localities")
    top_locs = df["location_text"].value_counts().head(10).reset_index()
    fig5 = px.bar(top_locs, x="count", y="location_text", orientation="h")
    st.plotly_chart(fig5, use_container_width=True)

with col6:
    st.subheader("Duplicate Filtered Status")
    status_counts = df["status"].value_counts().reset_index()
    fig6 = px.bar(status_counts, x="status", y="count", color="status")
    st.plotly_chart(fig6, use_container_width=True)
