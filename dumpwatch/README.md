# DumpWatch: Illegal Dumping Detection & Decision Support System

An end-to-end NLP & Spatial Decision Support System for detecting illegal garbage dumping, predicting risk zones, and routing municipal cleanup crews in Thane, Maharashtra.

## Architecture & Tech Stack
- **UI Framework:** Streamlit (Multipage)
- **NLP Classifier:** Hugging Face Transformers (`typeform/distilbert-base-uncased-mnli`)
- **Named Entity Recognition (NER):** spaCy (`en_core_web_sm` + custom EntityRuler for Thane localities)
- **Semantic Deduplication:** SentenceTransformers (`all-MiniLM-L6-v2`) + Haversine distance
- **Geocoding:** Geopy (Nominatim) with disk caching & rate limiting
- **Risk Prediction:** Scikit-Learn RandomForestRegressor on spatial 500m grid cells
- **Spatial Clustering:** DBSCAN with Haversine metric
- **Visualization:** Folium, Streamlit-Folium, Plotly Express
- **Storage:** TinyDB (default) with optional MongoDB Atlas support

---

## Folder Structure
```
dumpwatch/
  app.py
  config.py
  requirements.txt
  README.md
  data/
  scripts/generate_data.py
  src/
    preprocess.py
    classifier.py
    ner.py
    geocode.py
    dedup.py
    storage.py
    hotspot.py
    risk.py
    alerts.py
    decision.py
    vision.py
    pipeline.py
  pages/
    1_Live_Map.py
    2_Risk_Heatmap.py
    3_Analytics.py
    4_Decision_Support.py
  tests/
    test_pipeline.py
```

---

## How to Run
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   python -m spacy download en_core_web_sm
   ```
2. Generate synthetic data (optional, auto-runs on launch):
   ```bash
   python scripts/generate_data.py
   ```
3. Run Streamlit app:
   ```bash
   streamlit run app.py
   ```

---

## How to Demo

Use these 5 sample texts during presentation testing:

1. **Standard Illegal Dumping Report:**
   > `"Massive pile of plastic garbage and household waste dumped near Kopri station road!"`

2. **Hinglish Dumping Report:**
   > `"Bohot sara chemical waste aur kachra openly dumped near Wagle Estate drain."`

3. **High-Severity Medical Waste Report:**
   > `"Urgent! Syringes and hazardous medical waste dumped outside Kopri hospital gate!"`

4. **Duplicate Report Pair (Test with #1 above):**
   > `"Re-reporting again: plastic waste still lying unattended near Kopri station area!"`

5. **Unrelated Non-Dumping Complaint:**
   > `"Potholes on main Ghodbunder flyover causing heavy traffic congestion since morning."`
