# Antigravity Master Prompts: DumpWatch

## How to use these (credit-saving rules)

1. Run **one prompt at a time**, in order. Test it, then move on.
2. Use **Fast mode**, not Planning mode, for most prompts. Planning mode burns more quota.
3. Do **not** let the agent open the browser to test the app. Run `streamlit run app.py` yourself.
4. Every prompt ends with "Do not do anything beyond this scope". That stops it from wandering and spending credits.
5. If something breaks, paste only the error message and the file name, not the whole project.
6. Put Prompt 0 into Antigravity's Rules (or a `PROJECT_RULES.md` file in the project root) so it applies to every later prompt without repeating it.

Total: 1 rules file + 6 build prompts.

---

## PROMPT 0: Project Rules (set once, never repeat)

```
PROJECT: DumpWatch, an Illegal Dumping Detection and Decision Support System (NLP Complex Engineering Problem, Group-7).

STACK (do not substitute): Python 3.10+, Streamlit (multipage), Hugging Face Transformers (zero-shot classification), spaCy (NER), sentence-transformers (all-MiniLM-L6-v2), geopy (Nominatim), TinyDB (default storage) with optional MongoDB Atlas, scikit-learn, folium + streamlit-folium, plotly.

ARCHITECTURE: Input feeds (citizen text, social media, email/web form, image evidence) -> Preprocessing -> Classifier + NER -> Geocoding -> Duplicate detection -> Storage -> Hotspots/Risk/Alerts -> Streamlit dashboard with Live Map, Risk Heatmap, Analytics, Decision Support.

FOLDER STRUCTURE (strict):
dumpwatch/
  app.py, config.py, requirements.txt, README.md
  data/, scripts/generate_data.py
  src/: preprocess.py, classifier.py, ner.py, geocode.py, dedup.py, storage.py, hotspot.py, risk.py, alerts.py, decision.py, vision.py, pipeline.py
  pages/: 1_Live_Map.py, 2_Risk_Heatmap.py, 3_Analytics.py, 4_Decision_Support.py
  tests/test_pipeline.py

RULES:
- Keep code simple, readable, with short docstrings. No over-engineering.
- Every model loads once using st.cache_resource. Never reload per request.
- Geocoding must be cached to disk and rate limited to 1 request/second.
- Everything must run on a normal laptop CPU, no GPU, no paid API keys.
- Use lightweight models only. Do not download models larger than ~500 MB each.
- Never crash the UI: wrap external calls in try/except and show friendly messages.
- Only touch the files named in the current prompt.
- Do NOT open the browser or run the app. Do NOT write extra docs or summaries.
- Keep your reply short: list the files changed and nothing else.
```

---

## PROMPT 1: Scaffold + Synthetic Data

```
Create the full dumpwatch/ folder structure from the project rules, with empty placeholder files (just a docstring) for every file in src/ and pages/.

Then write these properly:
1. config.py: labels, thresholds, and paths. Include:
   - CLASSIFY_LABELS = ["illegal waste dumping", "garbage collection complaint", "sewage or water issue", "unrelated"]
   - WASTE_TYPES = ["household garbage", "construction debris", "industrial waste", "plastic waste", "medical waste", "e-waste", "organic waste"]
   - DEDUP_SIM_THRESHOLD = 0.80, DEDUP_RADIUS_M = 300, DEDUP_WINDOW_DAYS = 7
   - DEFAULT_CITY = "Thane, Maharashtra, India", default map center for Thane
   - file paths for data/, db, and geocode cache
2. scripts/generate_data.py: generate 600 synthetic reports for Thane using real Thane localities (Ghodbunder Road, Kopri, Naupada, Wagle Estate, Majiwada, Vartak Nagar, Kalwa, Mumbra, Diva, Kolshet etc. with approximate lat/lon).
   Columns: report_id, raw_text, source (citizen/twitter/email/form), locality, lat, lon, waste_type, severity (1-5), timestamp (last 120 days), has_image (bool), is_dumping (bool).
   - Make ~75% genuine dumping reports in varied natural phrasing (some Hinglish, some typos), ~25% unrelated or other complaints.
   - Create 4 clear hotspot localities with more incidents, and a slight upward trend in recent weeks.
   - Add ~40 intentional near-duplicate reports (same incident, different wording, same area, within 2 days).
   - Save to data/sample_reports.csv.
3. requirements.txt exactly as provided by me (I will paste it).

Do not do anything beyond this scope.
```

---

## PROMPT 2: NLP Core (Preprocess, Classifier, NER)

```
Implement the NLP core in src/preprocess.py, src/classifier.py, src/ner.py.

preprocess.py: clean_text(text) removes URLs, emojis, @mentions, extra whitespace, keeps hashtag words, normalizes case lightly (keep original for NER). Return both cleaned and original.

classifier.py:
- Use Hugging Face zero-shot-classification pipeline with a LIGHT model: "typeform/distilbert-base-uncased-mnli". Load via a cached function.
- classify_report(text) -> dict: {is_dumping: bool, label, confidence, waste_type, severity}
- Step 1: classify against CLASSIFY_LABELS. is_dumping = top label is "illegal waste dumping" and confidence > 0.5.
- Step 2: only if is_dumping, run a second zero-shot call against WASTE_TYPES.
- Severity (1-5): rule-based from keywords (medical, hazardous, burning, river, drain, school, hospital, huge, truckload push it up) plus waste type weight. Keep it as a small readable function.
- Add classify_batch(texts) for CSV uploads.

ner.py:
- Use spaCy en_core_web_sm plus an EntityRuler added BEFORE the ner component with patterns for Thane localities and common landmark words (e.g. "near X station", "behind X mall", "X road", "X nagar", "X naka", "X bridge"). Load locality list from config.
- extract_locations(text) -> list of strings, ranked: landmark/locality matches first, then GPE/LOC/FAC entities. Remove duplicates.
- Add a tiny regex fallback if spaCy finds nothing.

Add a small __main__ test block in each file with 3 example sentences. Do not do anything beyond this scope.
```

---

## PROMPT 3: Geocoding, Storage, Duplicate Detection, Pipeline

```
Implement src/geocode.py, src/storage.py, src/dedup.py, src/pipeline.py, src/vision.py.

geocode.py:
- geocode(place_text) using geopy Nominatim with user_agent "dumpwatch-group7". Append DEFAULT_CITY to the query. Rate limit 1 request/sec.
- Cache results in a JSON file (data/geocode_cache.json). If cached, return instantly.
- If it fails, fall back to the locality coordinates from config, else return None.

storage.py:
- Class Storage with a TinyDB backend by default and optional MongoDB backend picked via env var STORAGE_BACKEND. Same interface for both: insert_report, get_all, get_recent(days), update_status(report_id, status), count.
- Report document fields: report_id, raw_text, clean_text, source, timestamp, coordinates [lat, lon], location_text, waste_type, severity, status (Pending/Duplicate/Resolved), duplicate_of, semantic_embedding (list of floats), has_image.
- Function load_sample_csv() that runs the full pipeline over data/sample_reports.csv and fills the database (only if db is empty).

dedup.py:
- Load sentence-transformers all-MiniLM-L6-v2 (cached).
- embed(text).
- find_duplicate(new_embedding, new_coords, new_time, existing_reports): a report is a duplicate if cosine similarity >= DEDUP_SIM_THRESHOLD AND distance <= DEDUP_RADIUS_M (haversine) AND within DEDUP_WINDOW_DAYS. Return (is_duplicate, original_report_id, similarity). Use numpy vectorized similarity, no loops over embeddings.

vision.py (optional feature, must fail gracefully):
- check_image(pil_image) using CLIP "openai/clip-vit-base-patch32" zero-shot between ["a photo of illegally dumped garbage", "a clean street", "an unrelated photo"]. Return {shows_dumping: bool, confidence}. Lazy load only when an image is actually uploaded.

pipeline.py:
- process_report(raw_text, source, image=None, timestamp=None) runs: clean -> classify -> (if dumping) NER -> geocode -> embed -> dedup -> save -> return a result dict with all fields. If an image is given, include the vision result and boost severity slightly when it confirms dumping.
- Non-dumping reports are saved with status "Rejected" and not shown on maps.

Do not do anything beyond this scope.
```

---

## PROMPT 4: Hotspots, Risk Prediction, Alerts, Decision Support

```
Implement src/hotspot.py, src/risk.py, src/alerts.py, src/decision.py.

hotspot.py:
- find_hotspots(reports_df) uses DBSCAN with haversine metric (eps ~ 400 m, min_samples 4) on non-duplicate dumping reports. Return the dataframe with a cluster column plus a summary table: cluster_id, center lat/lon, incident count, avg severity, dominant waste type, nearest locality name.

risk.py:
- Divide Thane into a grid (about 500 m cells). Build a weekly table: cell, week, incident_count, avg_severity, previous 1-week and 2-week counts, rolling 4-week mean.
- Train a scikit-learn RandomForestRegressor to predict next-week incident count per cell. Time-based split (no shuffling). Report MAE.
- predict_risk() returns each cell with risk_score 0-100 and a level (Low/Medium/High/Critical). Return heatmap points [lat, lon, weight] for folium HeatMap.
- Cache the trained model in memory with st.cache_resource compatible functions. Keep it fast (under 5 seconds on 600 reports).

alerts.py:
- generate_alerts(reports_df, hotspots, risk) returns a list of alert dicts {level, title, message, location, time}. Rules: (a) severity >= 4 report in last 24h, (b) a hotspot whose last-7-day count is at least 1.5x its previous week, (c) any Critical risk cell, (d) medical or industrial waste reported anywhere.

decision.py:
- recommend_response(hotspot_or_report) returns {priority, crew_type, action, suggested_timeframe}. Rule-based scoring from severity, waste type, incident count, and risk level. Examples: medical waste -> hazmat crew within 6 hours; construction debris -> heavy truck + enforcement notice; household garbage -> regular crew + CCTV/fine recommendation if repeated.
- rank_priorities(hotspots) sorts by priority score so the municipality knows what to clear first. Add a simple optimized route order by nearest-neighbour starting from a depot coordinate in config.

Do not do anything beyond this scope.
```

---

## PROMPT 5: Streamlit Dashboard (all pages)

```
Build the Streamlit UI: app.py and the four files in pages/.

app.py (Home + Submit Report):
- Page title, short intro, and top KPI metrics (total reports, pending, duplicates removed, active alerts).
- On first launch, auto-load sample data if the db is empty (show a spinner).
- Tabs: "Submit single report" (text box, source dropdown, optional image upload, shows the pipeline result: classification, waste type, extracted location, severity, duplicate status), and "Bulk upload CSV" (upload CSV with a raw_text column, process with progress bar, show results table).
- Sidebar: a button to reload sample data and a button to clear the db.

pages/1_Live_Map.py: folium map centered on Thane, marker colors by status (Pending orange, Resolved green, Duplicate blue), popups with text, waste type, severity, time. Filters in sidebar: status, waste type, source, date range. A "Mark as resolved" action for a selected report.

pages/2_Risk_Heatmap.py: folium HeatMap of predicted risk plus hotspot cluster circles. Show a table of the top 10 high-risk zones and the model MAE.

pages/3_Analytics.py: plotly charts: incidents over time (weekly), waste type distribution, reports by source, severity distribution, duplicate removal rate, top 10 localities.

pages/4_Decision_Support.py: active alerts list (colored by level), then a prioritized hotspot table with recommended crew, action, timeframe, plus the suggested route order.

Design: clean, consistent, wide layout, simple custom CSS for cards. Use st.cache_data for heavy computations. Every page must handle an empty database without errors.

Do not do anything beyond this scope. Do not run the app.
```

---

## PROMPT 6: Tests + Final Polish (only when everything works)

```
1. Write tests/test_pipeline.py with 6 small pytest tests: classifier detects a clear dumping sentence, classifier rejects an unrelated sentence, NER extracts "Kopri" from a sample sentence, dedup flags two near-identical nearby reports, dedup does NOT flag the same text far away, hotspot function returns at least one cluster on the sample data.
2. Add a "How to demo" section to the end of README.md with 5 sample report texts to paste during the presentation (including one Hinglish, one duplicate pair, and one unrelated message).
3. Fix any import errors or obvious bugs you notice, minimal edits only.

Do not do anything beyond this scope.
```

---

## If something breaks (cheap fix prompt)

```
I got this error when running <command>:
<paste only the last 10-15 lines of the error>
Fix only the file that causes it. Do not refactor anything else. Reply with the file name changed only.
```

## Quick tips to save quota

- Skip Prompt 6 until your demo is close.
- If Prompt 3 or 5 feels too big for one go, split it at the file boundaries (geocode + storage, then dedup + pipeline).
- Run `python scripts/generate_data.py` and test each module's `__main__` block yourself between prompts.
- Use the **Fast** model option and avoid asking it to "review the whole project".
