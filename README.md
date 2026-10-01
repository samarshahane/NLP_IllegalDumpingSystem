# DumpWatch: Illegal Dumping Detection and Decision Support System

**NLP Complex Engineering Problem | Group-7**

An AI-driven system that collects illegal waste dumping reports from many channels, understands them using NLP, places them on a map, finds hotspots, removes duplicates, predicts risky zones, and recommends how a municipality should respond.

## Problem Statement

Illegal waste dumping reported through citizen complaints and social media often goes unnoticed because monitoring is manual. This causes environmental damage and slow municipal action.

**Goal:** Build a system that combines NLP, Machine Learning, GIS, computer vision (where image evidence exists) and predictive analytics to:

1. Collect reports from multiple channels
2. Classify illegal dumping incidents automatically
3. Extract dumping locations using Named Entity Recognition (NER)
4. Identify dumping hotspots
5. Detect duplicate reports
6. Predict high-risk dumping zones from historical patterns
7. Show real-time dashboards with alerts and optimized response recommendations

## Architecture

```
[1. Input Feeds]        [2. Core NLP Pipeline]         [3. Geo + Storage]        [4. Dashboard]
Citizen reports   -->   Preprocessing                  Geocoding (geopy)         Real-time map
Social media      -->   Zero-shot classifier     -->   TinyDB / MongoDB    -->   Risk heatmap
Email / web forms -->   Custom NER (spaCy)             (with embeddings)         Analytics panel
Image evidence    -->   Duplicate detection                                      Decision support
```

## Features

| Module | What it does | Tech |
|---|---|---|
| Ingestion | Accepts text, CSV, form input, optional image | Streamlit, pandas |
| Classification | Is it illegal dumping? What type of waste? | Hugging Face zero-shot |
| NER | Pulls out locations and landmarks | spaCy + EntityRuler |
| Geocoding | Converts place text to coordinates | geopy / Nominatim (cached) |
| Deduplication | Flags reports that describe the same incident | sentence-transformers + cosine similarity + distance + time window |
| Hotspots | Clusters incidents into hotspots | DBSCAN (haversine) |
| Risk prediction | Predicts next-week risk per grid cell | scikit-learn |
| Image check | Optional: does the photo show dumped waste? | CLIP zero-shot |
| Alerts | Flags hotspot spikes and high-severity reports | Rule-based |
| Decision support | Suggests crew, priority and action | Rule-based scoring |
| Dashboard | Map, heatmap, charts, alerts | Streamlit, folium, plotly |

## Project Structure

```
dumpwatch/
├── app.py                  # Streamlit entry point (home + report submission)
├── config.py               # labels, thresholds, paths
├── requirements.txt
├── README.md
├── data/
│   └── sample_reports.csv  # synthetic data (generated)
├── scripts/
│   └── generate_data.py    # creates synthetic reports
├── src/
│   ├── preprocess.py
│   ├── classifier.py
│   ├── ner.py
│   ├── geocode.py
│   ├── dedup.py
│   ├── storage.py
│   ├── hotspot.py
│   ├── risk.py
│   ├── alerts.py
│   ├── decision.py
│   ├── vision.py
│   └── pipeline.py         # runs one report through all steps
├── pages/
│   ├── 1_Live_Map.py
│   ├── 2_Risk_Heatmap.py
│   ├── 3_Analytics.py
│   └── 4_Decision_Support.py
└── tests/
    └── test_pipeline.py
```

## Setup

```bash
# 1. Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Mac/Linux

# 2. Install dependencies
pip install -r requirements.txt
python -m spacy download en_core_web_sm

# 3. Generate sample data
python scripts/generate_data.py

# 4. Run the app
streamlit run app.py
```

The first run downloads the Hugging Face models (about 1 GB total), so it takes a few minutes. After that they are cached.

### Optional: MongoDB Atlas

By default the app uses **TinyDB** (a local JSON file, no setup). To use MongoDB Atlas instead, create a `.env` file:

```
STORAGE_BACKEND=mongodb
MONGODB_URI=your_connection_string
```

## How It Works (Short)

1. A report comes in as text (and maybe an image).
2. Text is cleaned, then a zero-shot model decides if it is illegal dumping and what kind of waste.
3. The NER model pulls out the location and landmarks.
4. The location is converted to coordinates, cached to respect Nominatim limits.
5. The report is turned into an embedding and compared to recent nearby reports. High similarity means it is a duplicate.
6. The report is saved with its status (Pending, Duplicate, Resolved).
7. Hotspots and risk scores are recomputed, and alerts are raised if needed.
8. The dashboard shows everything live.

## Tech Stack

Python, Streamlit, Hugging Face Transformers, spaCy, sentence-transformers, scikit-learn, geopy, folium, plotly, TinyDB / MongoDB Atlas.

## Limitations

- Uses synthetic data for training and demo; real municipal data would improve accuracy.
- Free Nominatim geocoding is rate-limited (1 request per second), so results are cached.
- Zero-shot classification is less accurate than a fine-tuned model.
- Social media feeds are simulated through CSV upload, not live APIs.

## Team

**Group-7**, NLP Complex Engineering Problem

| Name | Roll No |
|---|---|
| | |
| | |
| | |
| | |

**Guide:** 
