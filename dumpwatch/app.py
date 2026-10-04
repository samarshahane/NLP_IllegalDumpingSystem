import base64
import os
import sys
import pandas as pd
from PIL import Image
import streamlit as st

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import config
from src.storage import (
    Storage,
    get_reports_df,
    get_waste_types,
    load_sample_csv,
    save_custom_waste_type,
    register_employee,
    authenticate_employee,
    get_all_employees,
)
from src.geocode import geocode
from src.pipeline import process_report
from src.vision import check_image
from src.classifier import calculate_severity

# Page Config
st.set_page_config(
    page_title="DumpWatch - AI Illegal Dumping Detection System",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Helper function to get base64 encoded background image
def get_base64_image(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    return ""

bg_img_path = os.path.join(config.BASE_DIR, "assets", "full_page_bg.png")
bg_b64 = get_base64_image(bg_img_path)

# Session State Initialization
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "user_emp" not in st.session_state:
    st.session_state["user_emp"] = {}
if "current_nav" not in st.session_state:
    st.session_state["current_nav"] = "HOME"
if "theme_mode" not in st.session_state:
    st.session_state["theme_mode"] = "dark"  # "dark" or "light"

bg_dark_path = os.path.join(config.BASE_DIR, "assets", "full_page_bg.png")
bg_light_path = os.path.join(config.BASE_DIR, "assets", "light_page_bg.jpg")
if not os.path.exists(bg_light_path):
    bg_light_path = os.path.join(config.BASE_DIR, "assets", "light_page_bg.png")

bg_dark_b64 = get_base64_image(bg_dark_path)
bg_light_b64 = get_base64_image(bg_light_path)

is_dark = st.session_state["theme_mode"] == "dark"
bg_b64 = bg_dark_b64 if is_dark else bg_light_b64

if is_dark:
    active_t = {
        "bg_overlay": "linear-gradient(180deg, rgba(13, 22, 18, 0.75) 0%, rgba(13, 22, 18, 0.90) 100%)",
        "app_text": "#ECFDF5",
        "hero_bg": "rgba(13, 26, 20, 0.80)",
        "hero_title": "#4ADE80",
        "card_bg": "rgba(22, 38, 31, 0.80)",
        "card_title": "#4ADE80",
        "card_text": "#CBD5E1",
        "border_color": "rgba(74, 222, 128, 0.3)",
        "status_bg": "#16261F",
        "status_border": "#22543D",
        "input_bg": "#16261F",
        "input_border": "#22543D",
        "input_text": "#ECFDF5",
        "btn_bg": "#16261F",
        "btn_text": "#ECFDF5",
        "btn_border": "rgba(74, 222, 128, 0.4)",
    }
else:
    active_t = {
        "bg_overlay": "linear-gradient(180deg, rgba(255, 255, 255, 0.15) 0%, rgba(240, 246, 244, 0.35) 100%)",
        "app_text": "#0F172A",
        "hero_bg": "rgba(255, 255, 255, 0.90)",
        "hero_title": "#047857",
        "card_bg": "rgba(255, 255, 255, 0.90)",
        "card_title": "#047857",
        "card_text": "#334155",
        "border_color": "rgba(16, 185, 129, 0.40)",
        "status_bg": "#FFFFFF",
        "status_border": "#A7F3D0",
        "input_bg": "#FFFFFF",
        "input_border": "#10B981",
        "input_text": "#0F172A",
        "btn_bg": "rgba(255, 255, 255, 0.95)",
        "btn_text": "#0F172A",
        "btn_border": "rgba(16, 185, 129, 0.45)",
    }

# Custom High-End Modern Styling (Full Page Background, Glassmorphism Cards)
st.markdown(f"""
<style>
/* Ensure background transparency so full-page wallpaper shines through */
div[data-testid="stAppViewContainer"], .main, div[data-testid="stHeader"] {{
    background: transparent !important;
}}

/* Full Page Background Image Setup */
.stApp {{
    background: {active_t['bg_overlay']},
                url("data:image/png;base64,{bg_b64}") !important;
    background-size: cover !important;
    background-position: center !important;
    background-attachment: fixed !important;
    color: {active_t['app_text']} !important;
    font-family: 'Inter', system-ui, -apple-system, sans-serif;
}}

/* Typography colors */
h1, h2, h3, h4, h5, h6, p, label, span {{
    color: {active_t['app_text']} !important;
}}

.block-container {{
    padding-top: 0.8rem !important;
    padding-bottom: 2rem !important;
    padding-left: 1rem !important;
    padding-right: 1rem !important;
    max-width: 1080px !important;
    margin: 0 auto !important;
    background: transparent !important;
}}

/* Completely hide sidebar element and remove left margin */
section[data-testid="stSidebar"] {{
    display: none !important;
    width: 0px !important;
}}

#MainMenu {{visibility: hidden;}}
footer {{visibility: hidden;}}
header {{visibility: hidden !important; display: none !important;}}
div[data-testid="stHeader"] {{display: none !important;}}
button[data-testid="baseButton-headerNoPadding"] {{display: none !important;}}
div[data-testid="collapsedControl"] {{display: none !important; visibility: hidden !important;}}
div[data-testid="stSidebarNav"] {{display: none !important;}}

/* Hero Section Container */
.hero-bg-section {{
    background: {active_t['hero_bg']};
    backdrop-filter: blur(12px);
    border-radius: 12px;
    padding: 30px 26px;
    color: {active_t['app_text']};
    margin-bottom: 18px;
    border: 1px solid {active_t['border_color']};
    box-shadow: 0 12px 30px rgba(0, 0, 0, 0.15);
}}

.hero-title {{
    font-size: 30px;
    font-weight: 800;
    letter-spacing: -0.5px;
    margin-bottom: 8px;
    color: {active_t['hero_title']};
}}

.hero-subtitle {{
    font-size: 14px;
    color: {active_t['app_text']};
    max-width: 700px;
    line-height: 1.5;
}}

/* Feature Cards - Compact & Glassmorphic */
.feature-card {{
    background: {active_t['card_bg']};
    backdrop-filter: blur(12px);
    border: 1px solid {active_t['border_color']};
    border-radius: 10px;
    padding: 16px;
    margin-bottom: 12px;
    transition: transform 0.2s ease, border-color 0.2s ease;
}}
.feature-card:hover {{
    border-color: {active_t['card_title']};
    transform: translateY(-2px);
}}

.feature-card h4 {{
    color: {active_t['card_title']};
    margin-top: 0;
    margin-bottom: 6px;
    font-size: 15px;
    font-weight: 700;
}}

.feature-card p {{
    color: {active_t['card_text']};
    font-size: 13px;
    margin-bottom: 0;
}}

/* Status Display Cards */
.status-card {{
    background: {active_t['status_bg']};
    border: 1px solid {active_t['status_border']};
    border-radius: 8px;
    padding: 16px;
    margin-top: 12px;
}}
.status-badge {{
    display: inline-block;
    padding: 4px 10px;
    border-radius: 4px;
    font-weight: 700;
    font-size: 12px;
    text-transform: uppercase;
}}
.badge-pending {{ background-color: #78350F; color: #FDE68A; }}
.badge-resolved {{ background-color: #064E3B; color: #A7F3D0; }}
.badge-duplicate {{ background-color: #1E3A8A; color: #BFDBFE; }}
.badge-rejected {{ background-color: #334155; color: #E2E8F0; }}

/* Button & Navbar Styling */
.stButton button {{
    height: auto !important;
    padding: 6px 12px !important;
    font-size: 12px !important;
    font-weight: 600 !important;
    border-radius: 6px !important;
    background-color: {active_t['btn_bg']} !important;
    color: {active_t['btn_text']} !important;
    border: 1px solid {active_t['btn_border']} !important;
}}

.stButton button[kind="primary"] {{
    background-color: #059669 !important;
    color: #FFFFFF !important;
    border-color: #059669 !important;
    box-shadow: 0 2px 8px rgba(5, 150, 105, 0.4) !important;
}}

/* BaseWeb Inputs, Textareas, Selectboxes & File Uploaders Overrides */
div[data-baseweb="input"],
div[data-baseweb="input"] > div,
div[data-baseweb="base-input"],
div[data-baseweb="textarea"],
div[data-baseweb="textarea"] > div,
div[data-baseweb="select"],
div[data-baseweb="select"] > div,
div[data-baseweb="select"] [role="combobox"],
.stTextInput > div > div,
.stTextArea > div > div,
.stSelectbox > div > div,
.stTextInput input,
.stTextArea textarea,
textarea,
input,
section[data-testid="stFileUploaderDropzone"],
button[data-testid="stFileUploaderDropzoneInput"],
div[data-testid="stFileUploader"] section {{
    background-color: {active_t['input_bg']} !important;
    border: 1px solid {active_t['input_border']} !important;
    color: {active_t['input_text']} !important;
}}

div[data-baseweb="input"] input,
div[data-baseweb="textarea"] textarea,
.stTextInput input,
.stTextArea textarea,
textarea,
input,
div[data-baseweb="select"] *,
div[data-baseweb="select"] span,
div[data-baseweb="select"] div,
div[data-baseweb="select"] svg,
section[data-testid="stFileUploaderDropzone"] *,
section[data-testid="stFileUploaderDropzone"] span,
section[data-testid="stFileUploaderDropzone"] div,
section[data-testid="stFileUploaderDropzone"] small {{
    color: {active_t['input_text']} !important;
}}

/* Specific styling for the file uploader Browse button */
section[data-testid="stFileUploaderDropzone"] button,
button[data-testid="stFileUploaderDropzoneInput"] {{
    background-color: {'#E2E8F0' if not is_dark else '#16261F'} !important;
    color: {active_t['input_text']} !important;
    border: 1px solid {active_t['input_border']} !important;
}}

section[data-testid="stFileUploaderDropzone"] button *,
button[data-testid="stFileUploaderDropzoneInput"] * {{
    color: {active_t['input_text']} !important;
}}

/* Clear, high-contrast placeholders */
::placeholder,
input::placeholder,
textarea::placeholder,
div[data-baseweb="select"] [aria-hidden="true"] {{
    color: {'#475569' if not is_dark else '#94A3B8'} !important;
    opacity: 0.9 !important;
    -webkit-text-fill-color: {'#475569' if not is_dark else '#94A3B8'} !important;
}}

/* Webkit text fill color override for inputs */
.stTextInput input, .stTextArea textarea, textarea, input {{
    -webkit-text-fill-color: {active_t['input_text']} !important;
}}

/* Radio options and sliders label text */
div[data-testid="stRadio"] label span,
div[data-testid="stSlider"] label span,
div[data-testid="stSelectbox"] label span,
div[data-testid="stTextArea"] label span,
div[data-testid="stTextInput"] label span {{
    color: {active_t['app_text']} !important;
}}

/* Dropdown Menu Item Overrides */
div[data-baseweb="popover"] ul,
div[data-baseweb="popover"] li,
div[data-baseweb="menu"] div {{
    background-color: {active_t['status_bg']} !important;
    color: {active_t['input_text']} !important;
}}
</style>
""", unsafe_allow_html=True)

storage = Storage()
csv_path = os.path.join(config.DATA_DIR, "reports.csv")
if not os.path.exists(csv_path) or os.path.getsize(csv_path) < 100:
    load_sample_csv()

# --- TOP NAVIGATION BAR & THEME CONTROL ---
toggle_btn_label = "☀️ Light Mode" if is_dark else "🌙 Dark Mode"

if st.session_state.get("authenticated", False):
    # ADMIN NAVBAR: Removed REGISTER COMPLAINT & TRACK APPLICATION
    nav_cols = st.columns([1, 1, 1, 1.1, 1.2, 0.9, 1.1])
    if nav_cols[0].button("HOME", use_container_width=True, type="primary" if st.session_state["current_nav"] == "HOME" else "secondary"):
        st.session_state["current_nav"] = "HOME"
        st.rerun()

    if nav_cols[1].button("LIVE MAP", use_container_width=True, type="primary" if st.session_state["current_nav"] == "LIVE MAP" else "secondary"):
        st.session_state["current_nav"] = "LIVE MAP"
        st.rerun()

    if nav_cols[2].button("HEATMAP", use_container_width=True, type="primary" if st.session_state["current_nav"] == "HEATMAP" else "secondary"):
        st.session_state["current_nav"] = "HEATMAP"
        st.rerun()

    if nav_cols[3].button("ANALYTICS", use_container_width=True, type="primary" if st.session_state["current_nav"] == "ANALYTICS" else "secondary"):
        st.session_state["current_nav"] = "ANALYTICS"
        st.rerun()

    if nav_cols[4].button("DISPATCH MATRIX", use_container_width=True, type="primary" if st.session_state["current_nav"] == "DISPATCH MATRIX" else "secondary"):
        st.session_state["current_nav"] = "DISPATCH MATRIX"
        st.rerun()

    if nav_cols[5].button("LOGOUT", use_container_width=True, type="secondary"):
        st.session_state["authenticated"] = False
        st.session_state["user_emp"] = {}
        st.session_state["current_nav"] = "HOME"
        st.rerun()

    if nav_cols[6].button(toggle_btn_label, use_container_width=True, type="secondary"):
        st.session_state["theme_mode"] = "light" if is_dark else "dark"
        st.rerun()

else:
    # PUBLIC NAVBAR
    nav_cols = st.columns([1, 1.3, 1.3, 1, 1.2, 1.1])
    if nav_cols[0].button("HOME", use_container_width=True, type="primary" if st.session_state["current_nav"] == "HOME" else "secondary"):
        st.session_state["current_nav"] = "HOME"
        st.rerun()

    if nav_cols[1].button("REGISTER COMPLAINT", use_container_width=True, type="primary" if st.session_state["current_nav"] == "REGISTER COMPLAINT" else "secondary"):
        st.session_state["current_nav"] = "REGISTER COMPLAINT"
        st.rerun()

    if nav_cols[2].button("TRACK APPLICATION", use_container_width=True, type="primary" if st.session_state["current_nav"] == "TRACK APPLICATION" else "secondary"):
        st.session_state["current_nav"] = "TRACK APPLICATION"
        st.rerun()

    if nav_cols[3].button("ABOUT", use_container_width=True, type="primary" if st.session_state["current_nav"] == "ABOUT" else "secondary"):
        st.session_state["current_nav"] = "ABOUT"
        st.rerun()

    if nav_cols[4].button("LOGIN / SIGN UP", use_container_width=True, type="primary" if st.session_state["current_nav"] == "LOGIN / SIGN UP" else "secondary"):
        st.session_state["current_nav"] = "LOGIN / SIGN UP"
        st.rerun()

    if nav_cols[5].button(toggle_btn_label, use_container_width=True, type="secondary"):
        st.session_state["theme_mode"] = "light" if is_dark else "dark"
        st.rerun()

st.markdown("<div style='margin-bottom:12px;'></div>", unsafe_allow_html=True)

# =============================================================================
# 1. HOME LANDING PAGE (WITH HERO BACKGROUND IMAGE)
# =============================================================================
if st.session_state["current_nav"] == "HOME":
    st.markdown("""
    <div class="hero-bg-section">
        <div class="hero-title">DumpWatch Municipal Intelligence</div>
        <div class="hero-subtitle">
            AI & NLP Driven Illegal Dumping Detection and Dispatch System for Thane Region. Real-time incident reporting, computer vision verification, and automated municipal routing.
        </div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    if st.session_state.get("authenticated", False):
        with c1:
            st.markdown("""
            <div class="feature-card">
                <h4>Live Map & Status Management</h4>
                <p>Monitor reported dumping locations across Thane in real time and manage resolution statuses.</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Open Live Map", type="primary", use_container_width=True):
                st.session_state["current_nav"] = "LIVE MAP"
                st.rerun()

        with c2:
            st.markdown("""
            <div class="feature-card">
                <h4>Risk Analytics & Heatmaps</h4>
                <p>Explore spatial hotspot predictions, category distributions, and automated crew dispatch routes.</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Open Analytics", type="secondary", use_container_width=True):
                st.session_state["current_nav"] = "ANALYTICS"
                st.rerun()
    else:
        with c1:
            st.markdown("""
            <div class="feature-card">
                <h4>Public Incident Reporting</h4>
                <p>Report illegal waste piles instantly. Citizens can provide landmark addresses, photo evidence, and waste descriptions without login.</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Register a Complaint", type="primary", use_container_width=True):
                st.session_state["current_nav"] = "REGISTER COMPLAINT"
                st.rerun()

        with c2:
            st.markdown("""
            <div class="feature-card">
                <h4>Application & Challan Tracking</h4>
                <p>Track the real-time resolution status of reported incidents using your unique Reference Application ID.</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Check Complaint Status", type="secondary", use_container_width=True):
                st.session_state["current_nav"] = "TRACK APPLICATION"
                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### About DumpWatch System")
    st.write("""
    DumpWatch leverages modern Natural Language Processing (DistilBERT zero-shot classification) and Computer Vision (OpenAI CLIP) to automate municipal waste detection. 
    By analyzing text descriptions and image evidence, the platform flags illegal dumping incidents, eliminates duplicate complaints, and predicts high-risk dumping zones across Thane city.
    """)

# =============================================================================
# 2. REGISTER COMPLAINT PAGE
# =============================================================================
elif st.session_state["current_nav"] == "REGISTER COMPLAINT":
    st.markdown("### Register a Waste Dumping Complaint")
    st.caption("Public Portal: No registration required. Please provide incident details below.")

    with st.container():
        raw_text = st.text_area(
            "Complaint Description (Required)",
            placeholder="Provide specific details, e.g. Large pile of plastic debris dumped near Kopri station market area.",
            height=90,
        )

        col_a, col_b = st.columns(2)
        with col_a:
            source = st.selectbox("Source Feed", ["Citizen Report", "Web Portal", "Social Media Alert", "Email Complaint"])
            waste_options = get_waste_types()
            waste_choice = st.selectbox("Waste Category", waste_options)
            if waste_choice == "Others":
                custom_waste = st.text_input("Specify Waste Description")
                final_waste = custom_waste.strip() if custom_waste.strip() else "household garbage"
            else:
                final_waste = waste_choice

        with col_b:
            loc_method = st.radio("Location Specification", ["Address / Landmark", "Manual Coordinates"], horizontal=True)
            if loc_method == "Address / Landmark":
                addr = st.text_input("Landmark or Area in Thane", placeholder="e.g. Wagle Estate, Ghodbunder Road")
                if addr.strip():
                    selected_coords = geocode(addr.strip())
                    selected_loc_text = addr.strip()
                    st.caption(f"Resolved Location: Lat {selected_coords[0]:.4f}, Lon {selected_coords[1]:.4f}")
                else:
                    selected_coords = list(config.DEFAULT_MAP_CENTER)
                    selected_loc_text = config.DEFAULT_CITY
            else:
                m_c1, m_c2 = st.columns(2)
                lat_in = m_c1.number_input("Latitude", value=float(config.DEFAULT_MAP_CENTER[0]), format="%.4f")
                lon_in = m_c2.number_input("Longitude", value=float(config.DEFAULT_MAP_CENTER[1]), format="%.4f")
                selected_coords = [lat_in, lon_in]
                selected_loc_text = f"{lat_in:.4f}, {lon_in:.4f}"

        auto_sev = calculate_severity(raw_text, final_waste) if raw_text.strip() else 3
        severity_val = st.slider("Estimated Severity Level (1 = Minor, 5 = Critical)", 1, 5, value=int(auto_sev))

        st.markdown("##### Photo Evidence (Optional)")
        f_up = st.file_uploader("Upload Image (JPG/PNG)", type=["jpg", "jpeg", "png"])
        uploaded_image = Image.open(f_up) if f_up else None

        if uploaded_image:
            st.image(uploaded_image, caption="Uploaded Evidence Preview", width=220)
            file_key = f"vision_res_{f_up.name}_{f_up.size}"
            if file_key not in st.session_state:
                try:
                    st.session_state[file_key] = check_image(uploaded_image)
                except Exception:
                    st.session_state[file_key] = {"shows_dumping": False, "confidence": 0.0}
            
            v_res = st.session_state[file_key]
            if v_res.get("shows_dumping"):
                st.success(f"Vision Verification: Dumping confirmed (Confidence: {v_res['confidence']:.0%})")
            elif v_res.get("confidence", 0) > 0:
                st.info("Vision Verification: No clear dumping pattern detected.")

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Submit Complaint", type="primary", use_container_width=True):
            if not raw_text.strip():
                st.error("Please provide an incident description before submitting.")
            else:
                if waste_choice == "Others" and final_waste != "household garbage":
                    save_custom_waste_type(final_waste)

                with st.spinner("Processing complaint and running AI classification..."):
                    try:
                        res = process_report(
                            raw_text=raw_text.strip(),
                            source=source.lower(),
                            image=uploaded_image,
                            forced_loc=selected_coords,
                            waste_type=final_waste,
                            severity=severity_val,
                        )
                        st.success("Complaint Successfully Registered!")
                        
                        st.markdown(f"""
                        <div class="status-card">
                            <h4 style="margin:0 0 6px 0; color:#4ADE80;">Application / Challan Reference ID: <strong>{res['report_id']}</strong></h4>
                            <p style="margin:0; color:#CBD5E1; font-size:13px;">Please save this Reference ID to track status in the <strong>TRACK APPLICATION</strong> tab.</p>
                        </div>
                        """, unsafe_allow_html=True)

                        c1, c2, c3, c4 = st.columns(4)
                        c1.metric("Status", res["status"])
                        c2.metric("Waste Type", res["waste_type"].title())
                        c3.metric("Severity Level", f"{res['severity']}/5")
                        c4.metric("Assigned Coords", f"{res['coordinates'][0]:.3f}, {res['coordinates'][1]:.3f}")

                    except Exception as e:
                        st.error(f"Failed to submit complaint: {e}")

# =============================================================================
# 3. TRACK APPLICATION PAGE
# =============================================================================
elif st.session_state["current_nav"] == "TRACK APPLICATION":
    st.markdown("### Track Complaint & Challan Status")
    st.caption("Enter your Application / Challan Reference ID to view live resolution updates.")

    col_id, col_btn = st.columns([3, 1])
    search_id = col_id.text_input("Application / Challan ID", placeholder="REP-XXXXXX").strip().upper()
    check_clicked = col_btn.button("Check Status", type="primary", use_container_width=True)

    if search_id or check_clicked:
        if not search_id:
            st.error("Please enter a valid Reference ID.")
        else:
            df = get_reports_df()
            if not df.empty and "report_id" in df.columns:
                match = df[df["report_id"].str.upper() == search_id]
                if not match.empty:
                    rec = match.iloc[0]
                    status_str = str(rec.get("status", "Pending"))
                    badge_class = f"badge-{status_str.lower()}"

                    st.markdown(f"""
                    <div class="status-card">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <h3 style="margin:0; color:#4ADE80;">Reference ID: {rec['report_id']}</h3>
                            <span class="status-badge {badge_class}">{status_str}</span>
                        </div>
                        <hr style="margin: 12px 0; border: none; border-top: 1px solid #22543D;">
                        <p><strong>Submission Date:</strong> {rec.get('timestamp', 'N/A')}</p>
                        <p><strong>Location:</strong> {rec.get('location_text', 'Thane')}</p>
                        <p><strong>Category:</strong> {str(rec.get('waste_type', 'General')).title()}</p>
                        <p><strong>Severity Level:</strong> {rec.get('severity', 3)} / 5</p>
                        <p><strong>Complaint Summary:</strong> {rec.get('raw_text', '')}</p>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.error(f"No complaint record found for Reference ID: {search_id}.")
            else:
                st.info("No records currently stored in system.")

# =============================================================================
# 4. ABOUT PAGE
# =============================================================================
elif st.session_state["current_nav"] == "ABOUT":
    st.markdown("### About DumpWatch System")
    st.markdown("""
    **DumpWatch** is an intelligent illegal waste detection and tracking platform created for Thane city. 
    It connects citizens reporting garbage issues directly with municipal cleaning teams to make neighborhood cleanup faster and more transparent.

    #### How DumpWatch Works (In Simple Words):

    1. **Easy Public Reporting**: Anyone can report an illegal garbage dump by describing the location or uploading a photo. No registration or password is required.
    
    2. **Smart Waste Classification**: The system automatically reads the description and photo to identify what kind of waste is dumped (like plastic bottles, household garbage, medical waste, or construction debris) and determines how urgent the cleanup is.
    
    3. **Prevents Duplicate Complaints**: If several neighbors report the exact same pile of trash, DumpWatch automatically groups them together under a single reference ticket so city officers aren't overwhelmed with duplicate tasks.
    
    4. **Prioritized Cleaning Routes**: Sanitation teams get a live action map and efficient routes to clean up high-risk areas (such as near schools, markets, or hospitals) first.
    
    5. **Transparent Status Tracking**: Every report receives a unique Reference ID (e.g. `REP-33D7E4`) so citizens can track when their complaint moves from **Pending** to **Resolved**.
    """)

# =============================================================================
# 5. ADMIN MODULES IN TOP BAR (LIVE MAP, HEATMAP, ANALYTICS, DISPATCH MATRIX)
# =============================================================================
elif st.session_state["current_nav"] == "LIVE MAP":
    import folium
    from streamlit_folium import st_folium
    st.markdown("### Live Incidents Map")

    df = get_reports_df()
    if df.empty:
        st.info("No incident records available.")
    else:
        m = folium.Map(location=config.DEFAULT_MAP_CENTER, zoom_start=config.DEFAULT_ZOOM)
        status_colors = {"Pending": "orange", "Resolved": "green", "Duplicate": "blue", "Rejected": "gray"}

        for _, row in df.iterrows():
            lat = row.get("lat", config.DEFAULT_MAP_CENTER[0])
            lon = row.get("lon", config.DEFAULT_MAP_CENTER[1])
            color = status_colors.get(row.get("status"), "orange")
            popup_content = f"<b>ID:</b> {row['report_id']}<br><b>Status:</b> {row['status']}<br><b>Category:</b> {row['waste_type']}<br><b>Severity:</b> {row['severity']}/5"
            folium.CircleMarker(location=[lat, lon], radius=6, color=color, fill=True, fill_color=color, popup=folium.Popup(popup_content, max_width=250)).add_to(m)

        st_folium(m, width=1000, height=480)

        st.markdown("#### Update Status")
        actionable_df = df[df["status"] != "Resolved"]
        if not actionable_df.empty:
            target_id = st.selectbox("Select Report ID to Update:", actionable_df["report_id"].unique(), format_func=lambda rid: f"{rid}  [{actionable_df[actionable_df['report_id']==rid]['status'].values[0]}]")
            new_status = st.selectbox("Set Status To:", ["Resolved", "Pending", "Rejected"])
            if st.button("Apply Status Update", type="primary"):
                storage.update_status(target_id, new_status)
                st.success(f"Report {target_id} status updated to {new_status}.")
                st.rerun()

elif st.session_state["current_nav"] == "HEATMAP":
    import folium
    from folium.plugins import HeatMap
    from streamlit_folium import st_folium
    from src.risk import predict_risk
    from src.hotspot import find_hotspots

    st.markdown("### Predicted Risk Heatmap & Hotspots")
    df = get_reports_df()
    if df.empty:
        st.info("No incident records available.")
    else:
        reports_data = storage.get_all()
        risk_df, heat_points, mae = predict_risk(reports_data)
        _, hotspots_summary = find_hotspots(df)

        m = folium.Map(location=config.DEFAULT_MAP_CENTER, zoom_start=config.DEFAULT_ZOOM)
        if heat_points:
            HeatMap(heat_points, radius=20, blur=15, max_zoom=13).add_to(m)
        st_folium(m, width=1000, height=480)

elif st.session_state["current_nav"] == "ANALYTICS":
    import plotly.express as px
    st.markdown("### Incident Analytics Dashboard")
    df = get_reports_df()
    if df.empty:
        st.info("No incident data available.")
    else:
        c1, c2 = st.columns(2)
        with c1:
            waste_counts = df["waste_type"].value_counts().reset_index()
            fig1 = px.pie(waste_counts, names="waste_type", values="count", title="Waste Type Distribution", hole=0.4)
            st.plotly_chart(fig1, use_container_width=True)
        with c2:
            status_counts = df["status"].value_counts().reset_index()
            fig2 = px.bar(status_counts, x="status", y="count", title="Incident Status Breakdown")
            st.plotly_chart(fig2, use_container_width=True)

elif st.session_state["current_nav"] == "DISPATCH MATRIX":
    from src.alerts import generate_alerts
    from src.decision import rank_priorities
    from src.hotspot import find_hotspots
    from src.risk import predict_risk

    st.markdown("### Crew Dispatch Matrix & Prioritized Routes")
    df = get_reports_df()
    if df.empty:
        st.info("No records available.")
    else:
        _, hotspots_summary = find_hotspots(df)
        ranked_hotspots = rank_priorities(hotspots_summary)
        if ranked_hotspots:
            ranked_df = pd.DataFrame(ranked_hotspots)
            display_cols = ["route_order", "locality", "priority", "crew_type", "action", "timeframe", "incident_count"]
            st.dataframe(ranked_df[display_cols], use_container_width=True)

# =============================================================================
# 6. LOGIN / SIGN UP (EMPLOYEE ADMIN DATABASE)
# =============================================================================
elif st.session_state["current_nav"] == "LOGIN / SIGN UP":
    st.markdown("### Admin & Backoffice Staff Portal")

    if st.session_state["authenticated"]:
        emp = st.session_state["user_emp"]
        st.success(f"Authenticated as: {emp.get('name', 'Admin')} (Employee ID: {emp.get('employee_id', '')}) | Role: {emp.get('role', 'Officer')}")
        st.info("Use the top navigation bar to access **LIVE MAP**, **HEATMAP**, **ANALYTICS**, and **DISPATCH MATRIX**.")

        df = get_reports_df()
        actionable_df = df[df["status"] != "Resolved"] if not df.empty else pd.DataFrame()

        st.markdown("#### Quick Status Update")
        if not actionable_df.empty:
            target_id = st.selectbox("Select Incident Reference ID:", actionable_df["report_id"].unique(), format_func=lambda rid: f"{rid}  [{actionable_df[actionable_df['report_id']==rid]['status'].values[0]}]")
            new_status = st.selectbox("Set Status To:", ["Resolved", "Pending", "Rejected"])
            if st.button("Apply Status Update", type="primary"):
                storage.update_status(target_id, new_status)
                st.success(f"Report {target_id} status updated to {new_status}.")
                st.rerun()
        else:
            st.success("All complaints have been resolved.")

    else:
        tab_login, tab_signup = st.tabs(["Employee Login", "Register Employee Account"])

        with tab_login:
            st.caption("Sign in using your registered Employee Number and Password.")
            with st.form("login_form"):
                emp_id_in = st.text_input("Employee Number", placeholder="e.g. EMP1001")
                pass_in = st.text_input("Password", type="password")
                submit_login = st.form_submit_button("Sign In", type="primary")

                if submit_login:
                    ok, emp_doc = authenticate_employee(emp_id_in, pass_in)
                    if ok:
                        st.session_state["authenticated"] = True
                        st.session_state["user_emp"] = emp_doc
                        st.session_state["current_nav"] = "LIVE MAP"
                        st.success(f"Welcome back, {emp_doc['name']}!")
                        st.rerun()
                    else:
                        st.error("Invalid Employee Number or Password. Default initial admin: EMP1001 / admin")

        with tab_signup:
            st.caption("Register a new municipal staff/admin account.")
            with st.form("signup_form"):
                reg_emp_id = st.text_input("Employee Number", placeholder="e.g. EMP1002")
                reg_name = st.text_input("Full Name", placeholder="e.g. Rajesh Kumar")
                reg_pass = st.text_input("Password", type="password")
                reg_role = st.selectbox("Role", ["Backoffice Officer", "Field Sanitation Inspector", "System Administrator"])
                submit_reg = st.form_submit_button("Register Account", type="primary")

                if submit_reg:
                    ok, msg = register_employee(reg_emp_id, reg_name, reg_pass, reg_role)
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)


