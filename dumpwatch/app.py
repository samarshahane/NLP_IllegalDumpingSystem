import os
import sys
import pandas as pd
from PIL import Image
import streamlit as st

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import config
from src.alerts import generate_alerts
from src.classifier import classify_report, calculate_severity
from src.geocode import geocode
from src.hotspot import find_hotspots
from src.pipeline import process_report
from src.risk import predict_risk
from src.storage import Storage, get_reports_df, get_waste_types, load_sample_csv, save_custom_waste_type
from src.vision import check_image

st.set_page_config(
    page_title="DumpWatch - Illegal Dumping Detection",
    page_icon="🗑️",
    layout="wide",
)

st.markdown("""
<style>
.main-header {
    background: linear-gradient(135deg, #1E2640 0%, #0F1423 100%);
    padding: 24px; border-radius: 12px; margin-bottom: 24px;
    border: 1px solid #2E3A59; box-shadow: 0 4px 12px rgba(0,0,0,0.25);
}
.header-title { color: #ECEFF4; font-size: 32px; font-weight: 700; margin-bottom: 4px; }
.header-tagline { color: #88C0D0; font-size: 16px; margin: 0; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="main-header">
    <div class="header-title">🗑️ DumpWatch</div>
    <div class="header-tagline">AI & NLP Driven Illegal Dumping Detection – Thane, Maharashtra (Group-7)</div>
</div>
""", unsafe_allow_html=True)

storage = Storage()

# Auto-seed sample data on first launch
csv_path = os.path.join(config.DATA_DIR, "reports.csv")
if not os.path.exists(csv_path) or os.path.getsize(csv_path) < 100:
    with st.spinner("Loading sample data for first launch..."):
        load_sample_csv()

# Sidebar
st.sidebar.title("🗑️ DumpWatch")
st.sidebar.caption("Group-7 NLP Complex Engineering Project")
st.sidebar.divider()

if st.sidebar.button("🔄 Reload Sample Data"):
    storage.clear()
    with st.spinner("Reloading..."):
        load_sample_csv()
    st.rerun()

reports_df = get_reports_df()
if not reports_df.empty:
    csv_data = reports_df.to_csv(index=False).encode("utf-8")
    st.sidebar.download_button("📥 Export CSV", data=csv_data,
                               file_name="dumpwatch_export.csv", mime="text/csv")

# KPI Metrics
total = len(reports_df)
pending = int((reports_df["status"] == "Pending").sum()) if not reports_df.empty else 0
dupes = int((reports_df["status"] == "Duplicate").sum()) if not reports_df.empty else 0
alerts_count = 0
if not reports_df.empty:
    try:
        _, hs = find_hotspots(reports_df)
        risk_df, _, _ = predict_risk(storage.get_all())
        alerts_count = len(generate_alerts(reports_df, hs, risk_df))
    except Exception:
        alerts_count = 0

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Reports", total)
c2.metric("Pending Complaints", pending)
c3.metric("Duplicates Removed", dupes)
c4.metric("Active Alerts", alerts_count)

st.divider()

tab1, tab2 = st.tabs(["📝 Submit Single Report", "📁 Bulk Upload CSV"])

# ─── TAB 1: Submit Single Report ─────────────────────────────────────────────
with tab1:
    st.subheader("Report an Illegal Dumping Incident")

    # Description
    raw_text = st.text_area(
        "Complaint Description *(required)*",
        placeholder="e.g. Large pile of plastic waste dumped near Kopri station road!",
        height=100,
    )

    # Source
    source = st.selectbox("Source Feed", ["citizen", "social media", "email", "web form"])

    # Photo Evidence
    st.markdown("**📷 Photo Evidence (Optional)**")
    img_method = st.radio("Upload method", ["📁 File Upload", "📷 Live Camera"], horizontal=True, label_visibility="collapsed")
    uploaded_image = None
    if img_method == "📁 File Upload":
        f_up = st.file_uploader("Upload JPG/PNG", type=["jpg", "jpeg", "png"], label_visibility="collapsed")
        if f_up:
            uploaded_image = Image.open(f_up)
    else:
        c_up = st.camera_input("Capture photo", label_visibility="collapsed")
        if c_up:
            uploaded_image = Image.open(c_up)

    if uploaded_image:
        st.image(uploaded_image, caption="Evidence Preview", width=280)
        try:
            v_res = check_image(uploaded_image)
            if v_res["shows_dumping"]:
                st.success(f"✅ AI Vision: Dumping confirmed (confidence {v_res['confidence']:.0%})")
            else:
                st.info("ℹ️ AI Vision: No clear dumping detected in image.")
        except Exception:
            pass

    # Location — Radio selector, no tab scoping issues
    st.markdown("**📍 Location**")
    loc_method = st.radio(
        "How to set location?",
        ["🔍 Type Address / Landmark", "🌐 Enter Coordinates Manually"],
        horizontal=True,
    )

    selected_coords = list(config.DEFAULT_MAP_CENTER)
    selected_loc_text = config.DEFAULT_CITY

    if loc_method == "🔍 Type Address / Landmark":
        addr = st.text_input(
            "Address or Landmark in Thane",
            placeholder="e.g. Kopri station, Ghodbunder Road, Wagle Estate",
        )
        if addr.strip():
            selected_loc_text = addr.strip()
            with st.spinner("Geocoding location..."):
                selected_coords = geocode(addr.strip())
            st.caption(f"📌 Coordinates resolved: {selected_coords[0]:.5f}, {selected_coords[1]:.5f}")
        else:
            st.caption("ℹ️ Leave blank to auto-extract location from the text using NER.")
    else:
        mc1, mc2 = st.columns(2)
        lat_in = mc1.number_input("Latitude", value=float(config.DEFAULT_MAP_CENTER[0]), format="%.5f")
        lon_in = mc2.number_input("Longitude", value=float(config.DEFAULT_MAP_CENTER[1]), format="%.5f")
        selected_coords = [lat_in, lon_in]
        selected_loc_text = f"{lat_in:.4f}, {lon_in:.4f}"

    # Waste Type
    waste_options = get_waste_types()
    waste_choice = st.selectbox("Waste Type", waste_options)
    if waste_choice == "Others":
        custom_waste = st.text_input("Specify waste type")
        final_waste = custom_waste.strip() if custom_waste.strip() else "household garbage"
    else:
        final_waste = waste_choice

    # Severity
    auto_sev = calculate_severity(raw_text, final_waste) if raw_text.strip() else 3
    severity_val = st.slider("Severity Level (1 = Minor, 5 = Critical)", 1, 5, value=int(auto_sev))

    st.divider()

    # Submit button — outside any form/tab so it always has access to all widget values
    submit_clicked = st.button("🚀 Submit Complaint", type="primary", use_container_width=True)

    if submit_clicked:
        if not raw_text.strip():
            st.error("⚠️ Please enter a complaint description.")
        else:
            if waste_choice == "Others" and final_waste != "household garbage":
                save_custom_waste_type(final_waste)

            with st.spinner("Running NLP pipeline... please wait."):
                try:
                    res = process_report(
                        raw_text=raw_text.strip(),
                        source=source,
                        image=uploaded_image,
                        forced_loc=selected_coords,
                        waste_type=final_waste,
                        severity=severity_val,
                    )
                    st.success(f"✅ Report Submitted! ID: **{res['report_id']}**")
                    col_r1, col_r2, col_r3, col_r4 = st.columns(4)
                    col_r1.metric("Status", res["status"])
                    col_r2.metric("Waste Type", res["waste_type"].title())
                    col_r3.metric("Severity", f"{res['severity']}/5")
                    col_r4.metric("Coords", f"{res['coordinates'][0]:.3f}, {res['coordinates'][1]:.3f}")
                    if res["status"] == "Duplicate":
                        st.warning(f"⚠️ Flagged as duplicate of report **{res['duplicate_of']}**")
                    elif res["status"] == "Rejected":
                        st.warning("ℹ️ Report classified as unrelated (not a dumping incident).")
                except Exception as e:
                    st.error(f"Pipeline error: {e}")

# ─── TAB 2: Bulk CSV Upload ───────────────────────────────────────────────────
with tab2:
    st.subheader("Bulk Process CSV Complaints")
    bulk_file = st.file_uploader(
        "Upload CSV file (must have `raw_text` column; optional: `source`, `waste_type`, `severity`)",
        type=["csv"], key="bulk_csv",
    )
    if bulk_file:
        b_df = pd.read_csv(bulk_file)
        if "raw_text" not in b_df.columns:
            st.error("CSV must contain a `raw_text` column.")
        else:
            st.write(f"Found **{len(b_df)} rows**. Preview:")
            st.dataframe(b_df.head(5), use_container_width=True)
            if st.button("▶️ Process All Rows"):
                prog = st.progress(0)
                tot = len(b_df)
                for idx, row in b_df.iterrows():
                    try:
                        process_report(
                            raw_text=str(row["raw_text"]),
                            source=str(row.get("source", "citizen")),
                            waste_type=str(row["waste_type"]) if "waste_type" in row and pd.notnull(row["waste_type"]) else None,
                            severity=int(row["severity"]) if "severity" in row and pd.notnull(row["severity"]) else None,
                        )
                    except Exception:
                        pass
                    prog.progress((idx + 1) / tot)
                st.success(f"✅ Bulk processed {tot} reports and saved to CSV/DB.")
                st.rerun()

st.divider()

# Recent Reports table
st.subheader("📋 Recent Reports")
reports_df = get_reports_df()
if not reports_df.empty:
    disp = reports_df.sort_values("timestamp", ascending=False).head(10)
    show_cols = [c for c in ["report_id", "timestamp", "source", "waste_type", "severity", "location_text", "status"] if c in disp.columns]
    st.dataframe(disp[show_cols], use_container_width=True)
else:
    st.info("No reports yet. Use the Submit tab above or click 'Reload Sample Data' in the sidebar.")
