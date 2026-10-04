import os
import sys
import pandas as pd
import streamlit as st

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.alerts import generate_alerts
from src.decision import rank_priorities
from src.hotspot import find_hotspots
from src.risk import predict_risk
from src.storage import Storage, get_reports_df

st.set_page_config(page_title="Decision Support - DumpWatch Enterprise", layout="wide")

# Check Auth
if not st.session_state.get("authenticated", False):
    st.warning("Restricted Page: Backoffice / Admin authentication required. Please log in from the main portal.")
    st.stop()

st.title("Decision Support & Crew Dispatch Matrix")

df = get_reports_df()

if df.empty:
    st.info("No incident records available.")
    st.stop()

storage = Storage()
reports_data = storage.get_all()

_, hotspots_summary = find_hotspots(df)
risk_df, _, _ = predict_risk(reports_data)
alerts = generate_alerts(df, hotspots_summary, risk_df)

st.subheader("Active Critical Alerts")
if alerts:
    for alert in alerts:
        color = "#991B1B" if alert["level"] == "Critical" else "#C2410C"
        st.markdown(
            f"""
            <div style="background-color:{color}; padding:14px; border-radius:6px; margin-bottom:10px; color:white;">
                <h4 style="margin:0;">[{alert['level']}] {alert['title']}</h4>
                <p style="margin:4px 0 0 0;">{alert['message']}</p>
                <small><b>Location:</b> {alert['location']} | <b>Time:</b> {alert['time']}</small>
            </div>
            """,
            unsafe_allow_html=True,
        )
else:
    st.success("No active critical alerts.")

st.divider()

st.subheader("Prioritized Hotspots & TSP Route Order")
ranked_hotspots = rank_priorities(hotspots_summary)

if ranked_hotspots:
    ranked_df = pd.DataFrame(ranked_hotspots)
    display_cols = ["route_order", "locality", "priority", "crew_type", "action", "timeframe", "incident_count", "dominant_waste"]
    st.dataframe(ranked_df[display_cols], use_container_width=True)
    st.caption("Route order optimized via Nearest-Neighbor TSP starting from central municipal depot.")
else:
    st.info("No active hotspot clusters detected.")

