# DumpWatch: Technical Architecture & Machine Learning Documentation

This document provides a comprehensive technical breakdown of **DumpWatch**, detailing the roles of every technology, machine learning model, natural language processing (NLP) pipeline, and geospatial algorithm used in the platform.

---

## 1. Executive System Overview

DumpWatch is an intelligent, multi-modal **Decision Support & NLP System** designed for municipal waste management. It automates the ingestion, validation, deduplication, spatial risk mapping, and dispatch routing of illegal waste dumping complaints in **Thane, Maharashtra**.

```
               +-------------------------------------------------+
               |              Citizen Report Input               |
               |       (Text Description + Photo Evidence)        |
               +-------------------------------------------------+
                                       |
                                       v
               +-------------------------------------------------+
               |       1. AI Vision Verification (CLIP)          |
               |  (Checks if photo shows actual waste debris)    |
               +-------------------------------------------------+
                                       |
                                       v
               +-------------------------------------------------+
               |   2. Zero-Shot NLP Classifier (DistilBERT)      |
               |  (Determines if complaint is illegal dumping)   |
               +-------------------------------------------------+
                                       |
                                       v
               +-------------------------------------------------+
               |  3. Named Entity Recognition (spaCy + Custom)   |
               | (Parses Thane localities & geocodes via Geopy)  |
               +-------------------------------------------------+
                                       |
                                       v
               +-------------------------------------------------+
               | 4. Semantic & Spatial Deduplication (MiniLM)    |
               |  (Flags duplicates via Embeddings + Haversine)  |
               +-------------------------------------------------+
                                       |
                                       v
               +-------------------------------------------------+
               | 5. Spatial Hotspot & Risk Modeling (DBSCAN/RF)  |
               |  (Grid risk scoring & truck route optimization) |
               +-------------------------------------------------+
```

---

## 2. Technology & Model Breakdown

### A. Natural Language Processing (NLP) & Text Models

#### 1. Zero-Shot Intent Classifier: Hugging Face Transformers (`typeform/distilbert-base-uncased-mnli`)
- **Role**: Automatically determines whether a text description represents an illegal waste dumping complaint vs. an unrelated issue (e.g., traffic congestion, potholes, noise complaints).
- **How it works**: Uses **Natural Language Inference (NLI)**. Instead of requiring task-specific model fine-tuning, the model compares the input text against candidate hypotheses:
  - *Premise*: `"Massive pile of plastic garbage dumped near Kopri station!"`
  - *Hypothesis*: `"This text is about illegal waste dumping."`
- **Fallback**: Incorporates a rapid keyword matching engine for instant pre-filtering of waste-related terms (*"garbage"*, *"kachra"*, *"dumped"*, *"waste"*, *"debris"*).

#### 2. Named Entity Recognition (NER): spaCy (`en_core_web_sm` + `EntityRuler`)
- **Role**: Extracts location names, landmarks, and street names from free-text citizen complaints.
- **How it works**: 
  - Uses spaCy's pre-trained English statistical model (`en_core_web_sm`) to identify `GPE` (Geopolitical Entity) and `FAC` (Facility) entities.
  - Enhanced with a custom **`EntityRuler`** pipeline component pre-loaded with Thane-specific localities (*Wagle Estate*, *Kopri*, *Ghodbunder Road*, *Naupada*, *Majiwada*, *Vartak Nagar*, etc.) to support Hinglish and informal local references.

#### 3. Semantic Embedding Model: SentenceTransformers (`sentence-transformers/all-MiniLM-L6-v2`)
- **Role**: Generates dense 384-dimensional vector embeddings for text complaints to detect duplicate reports.
- **How it works**: Converts text into vector representations where semantically similar descriptions (e.g., *"plastic waste dumped near market"* and *"bottles and trash thrown near market"*) yield high Cosine Similarity scores ($> 0.75$), even when different words are used.

---

### B. Computer Vision & Multi-Modal Verification

#### 1. Zero-Shot Image Classifier: OpenAI CLIP (`openai/clip-vit-base-patch32`)
- **Role**: Visually inspects user-uploaded photo evidence to verify if the image actually shows garbage/waste.
- **How it works**: CLIP (Contrastive Language-Image Pre-training) maps images and text into a shared embedding space. It evaluates uploaded images against visual text prompts:
  - `"a photo of illegally dumped garbage"` vs. `"a clean street"` vs. `"an unrelated photo"`.
- **Purpose**: Prevents fake or spam reports from polluting the municipal database.

---

### C. Geospatial Intelligence & Machine Learning

#### 1. Geocoding Engine: Geopy (`Nominatim`) + Disk Cache
- **Role**: Converts parsed location text strings into precise GPS coordinates (Latitude & Longitude).
- **Optimization**: Features an in-memory and JSON disk caching system (`geocode_cache.json`) with Nominatim rate-limiting to prevent redundant API calls and optimize performance.

#### 2. Spatial Proximity: Haversine Formula
- **Role**: Computes the exact great-circle distance (in meters/kilometers) between two GPS coordinate points on Earth.
- **Formula**:
  $$d = 2r \arcsin\left(\sqrt{\sin^2\left(\frac{\Delta \phi}{2}\right) + \cos(\phi_1)\cos(\phi_2)\sin^2\left(\frac{\Delta \lambda}{2}\right)}\right)$$
- **Application**: Combined with semantic embeddings to classify reports as **Duplicates** if they occur within **300 meters** of an existing open report and share high text similarity.

#### 3. Spatial Hotspot Clustering: Scikit-Learn `DBSCAN`
- **Role**: Automatically discovers high-density clusters of illegal dumping incidents across the city.
- **Why DBSCAN**: Unlike K-Means, Density-Based Spatial Clustering of Applications with Noise (DBSCAN) does not require pre-specifying the number of clusters and naturally identifies isolated noise points.
- **Metric**: Configured with Haversine distance (`eps = 0.5 km`, `min_samples = 3`).

#### 4. Predictive Risk Modeling: Scikit-Learn `RandomForestRegressor`
- **Role**: Predicts risk levels ($1.0$ to $5.0$) across a 500m x 500m spatial grid overlaying Thane.
- **Features**: Uses historical incident count, average severity score, and recent complaint frequency per grid cell to train an ensemble of decision trees.

---

### D. User Interface & Infrastructure

#### 1. Streamlit
- Multi-page application framework managing stateful navigation, interactive widgets, reactive UI updates, and session authentication.

#### 2. Folium & Streamlit-Folium
- Renders interactive Leaflet GIS maps featuring custom color-coded status markers, radius overlays, and heatmap layers (`HeatMap`).

#### 3. Plotly Express
- Powers interactive dashboard charts (incident breakdown by category, weekly trends, severity distribution).

#### 4. TinyDB / JSON Database
- Lightweight, file-based document store managing report records (`reports.csv`), employee registries (`employees.json`), and system logs.

---

## 3. Step-by-Step Execution Workflow ("What Happens")

When a user submits a complaint on DumpWatch:

1. **Submission**: User inputs text, selects severity (1-5), provides landmark/address, and optionally attaches a photo.
2. **Vision Check**: If a photo is attached, CLIP checks if it shows waste. If confidence $< 0.40$, a warning flag is raised.
3. **Intent Classification**: DistilBERT evaluates whether the text describes illegal dumping. Non-dumping complaints are flagged for review.
4. **Location Extraction & Geocoding**: spaCy NER extracts local landmarks; Geopy converts them to GPS coordinates.
5. **Deduplication Engine**:
   - Calculates semantic similarity ($S_{text}$) with existing reports using `all-MiniLM-L6-v2`.
   - Calculates geographic distance ($D_{geo}$) using Haversine.
   - If $S_{text} > 0.75$ and $D_{geo} < 300\text{ meters}$, status is set to **Duplicate** referencing the original report ID. Otherwise, status defaults to **Pending**.
6. **Database Persistence**: Report is saved to TinyDB / CSV with auto-generated ID (e.g. `REP-37A8D5`).
7. **Spatial Analysis**: DBSCAN recalculates active hotspots; Random Forest updates risk predictions.
8. **Admin Operations**: Municipal dispatchers view prioritized route maps connecting critical complaint clusters.

---

## 4. Summary Matrix

| Module | Primary Technology | Purpose |
| :--- | :--- | :--- |
| **UI & Dashboard** | Streamlit | Interactive citizen & admin Web App |
| **Intent Classifier** | Hugging Face (`DistilBERT`) | Zero-shot text dumping classification |
| **Vision Verification** | OpenAI `CLIP` | Photo evidence validation |
| **NER Location Parser** | spaCy (`en_core_web_sm` + `EntityRuler`) | Extract Thane localities & street names |
| **Text Embeddings** | SentenceTransformers (`all-MiniLM-L6-v2`) | Dense semantic similarity vectors |
| **Spatial Distance** | Haversine Formula | Precise geographical proximity in meters |
| **Geocoding** | Geopy (`Nominatim`) | Landmark string to GPS coordinates |
| **Hotspot Clustering** | Scikit-Learn `DBSCAN` | Density-based incident clustering |
| **Risk Prediction** | Scikit-Learn `RandomForest` | 500m grid cell risk score forecasting |
| **Mapping & GIS** | Folium / Leaflet | Real-time map & heatmap rendering |
| **Storage** | TinyDB / CSV | Persistent document record database |
