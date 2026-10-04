# DumpWatch: Smart AI-Powered Illegal Dumping Detection & Decision Support System

DumpWatch is an end-to-end NLP, Computer Vision, and Geospatial Intelligence system designed to streamline municipal waste management and combat illegal garbage dumping in **Thane, Maharashtra**.

The platform empowers citizens to report illegal dumping incidents while enabling city administrators to automatically classify complaints, eliminate duplicate reports, predict high-risk dumping zones, and optimize cleanup crew dispatch routes.

---

## Key Capabilities & Features

1. **Citizen Complaint Portal & AI Vision Verification**
   - **Zero-Shot NLP Classification**: Automatically determines whether a text complaint is related to illegal waste dumping using Hugging Face Transformers (`DistilBERT`).
   - **Image Evidence Inspection**: Uses OpenAI CLIP (`open-clip-torch`) to visually verify if uploaded images contain actual waste debris before processing.
   - **Multi-lingual / Hinglish Processing**: Supports English and Hinglish complaint descriptions (e.g., *"Bohot sara chemical waste dumped near Kopri station"*).

2. **Automated Location Extraction & Deduplication**
   - **Custom NER Location Parsing**: Built using spaCy (`en_core_web_sm`) and a custom `EntityRuler` to extract Thane landmarks, streets, and areas (e.g., *Wagle Estate*, *Kopri*, *Ghodbunder Road*).
   - **Semantic & Spatial Deduplication**: Combines Sentence Transformers (`all-MiniLM-L6-v2`) semantic similarity with Haversine spatial proximity matching to merge duplicate reports.

3. **Geospatial Analytics & Live Interactive Map**
   - **Real-Time Live Map**: Interactive Folium map displaying color-coded markers for pending, resolved, and duplicate complaints across Thane.
   - **DBSCAN Spatial Hotspot Clustering**: Groups nearby dumping incidents to highlight high-density problem areas.

4. **Predictive Risk Heatmap & Municipal Decision Support**
   - **Random Forest Risk Modeling**: Predicts 500m x 500m grid cell risk levels across the city based on historical incident density and severity.
   - **Automated Dispatch Routing**: Generates optimal cleanup truck routes connecting high-priority incident hotspots.
   - **Admin Management Portal**: Authenticated dashboard allowing city officials to review, update report statuses, and generate PDF/CSV summary reports.

5. **Dynamic UI Theme Engine**
   - Seamless **Light Mode** and **Dark Mode** toggling with high-contrast text legibility and custom smart-city wallpaper backgrounds.

---

## Tech Stack & Libraries

- **Frontend & App Framework**: Streamlit (Multipage architecture)
- **Natural Language Processing**: Hugging Face `transformers`, `sentence-transformers`, `spaCy`
- **Computer Vision**: OpenAI `open_clip_torch`, `torchvision`, `Pillow`
- **Geospatial & Mapping**: `folium`, `streamlit-folium`, `geopy`
- **Machine Learning & Analytics**: `scikit-learn` (Random Forest, DBSCAN), `pandas`, `numpy`, `plotly`
- **Database Storage**: TinyDB / JSON document storage
- **Containerization**: Docker

---

## Project Structure

```
dumpwatch/
├── app.py                      # Main Streamlit application entry point & Citizen Portal
├── config.py                   # Global configuration settings & directory paths
├── requirements.txt            # Python dependencies (includes direct spaCy model link)
├── Dockerfile                  # Production Docker container configuration
├── README.md                   # Project documentation
├── assets/                     # UI background images & assets
├── data/                       # Reports database, employee lookup, and cached geocodes
├── pages/
│   ├── 1_Live_Map.py           # Interactive GIS incident map
│   ├── 2_Risk_Heatmap.py       # Predictive risk density map
│   ├── 3_Analytics.py          # Municipal metrics & breakdown graphs
│   └── 4_Decision_Support.py   # Admin dispatch routing & report management
├── src/                        # Core backend processing modules
│   ├── classifier.py           # NLP zero-shot intent classifier
│   ├── vision.py               # CLIP vision verification model
│   ├── ner.py                  # spaCy location parser for Thane
│   ├── dedup.py                # Semantic & spatial duplicate detector
│   ├── geocode.py              # Geocoding & coordinate lookup
│   ├── pipeline.py             # End-to-end report pipeline handler
│   ├── hotspot.py              # DBSCAN spatial clustering
│   ├── risk.py                 # Random Forest risk prediction
│   ├── decision.py             # Route planning & dispatch engine
│   └── storage.py              # TinyDB database manager
└── scripts/
    └── generate_data.py        # Synthetic dataset generator for Thane
```

---

## How to Run Locally

### Prerequisites
- Python 3.10 or higher installed.

### Installation Steps

1. **Clone the repository**:
   ```bash
   git clone https://github.com/samarshahane/NLP_IllegalDumpingSystem.git
   cd NLP_IllegalDumpingSystem/dumpwatch
   ```

2. **Create and activate a virtual environment**:
   - **Windows (PowerShell)**:
     ```powershell
     python -m venv venv
     .\venv\Scripts\Activate
     ```
   - **macOS / Linux**:
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   python -m spacy download en_core_web_sm
   ```

4. **Launch the Streamlit App**:
   ```bash
   streamlit run app.py
   ```
   Open your browser and navigate to `http://localhost:8501`.

---

## How to Run via Docker

1. **Build the Docker Image**:
   ```bash
   docker build -t dumpwatch .
   ```

2. **Run the Docker Container**:
   ```bash
   docker run -p 8501:8501 dumpwatch
   ```
   Access the app at `http://localhost:8501`.

---

## Sample Test Complaints for Presentation & Demo

You can test the system live using these sample complaint scenarios:

1. **Standard Dumping Complaint**:
   > *"Large pile of plastic bottles and household garbage dumped openly near Kopri station market area."*

2. **Hinglish Complaint**:
   > *"Bohot sara chemical waste aur kachra dumped openly near Wagle Estate drain."*

3. **Urgent Medical Waste Complaint**:
   > *"Urgent! Syringes and hazardous medical waste dumped outside Kopri hospital gate!"*

4. **Duplicate Complaint Pair** (Test immediately after submitting #1 above):
   > *"Re-reporting again: plastic waste still lying unattended near Kopri station area!"*

5. **Irrelevant / Non-Dumping Complaint** (Tests AI filtering):
   > *"Heavy traffic congestion and deep potholes on main Ghodbunder flyover since morning."*

---

## Admin Portal Login Credentials

To access the municipal administrative dashboard:
- **Role**: Administrator
- **Password**: `admin123`
