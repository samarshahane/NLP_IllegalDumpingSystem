import os

# Classification & NLP Settings
CLASSIFY_LABELS = [
    "illegal waste dumping",
    "garbage collection complaint",
    "sewage or water issue",
    "unrelated",
]

WASTE_TYPES = [
    "household garbage",
    "construction debris",
    "industrial waste",
    "plastic waste",
    "medical waste",
    "e-waste",
    "organic waste",
]

# Deduplication Settings
DEDUP_SIM_THRESHOLD = 0.80
DEDUP_RADIUS_M = 300
DEDUP_WINDOW_DAYS = 7

# Location & Map Defaults (Thane, Maharashtra)
DEFAULT_CITY = "Thane, Maharashtra, India"
DEFAULT_MAP_CENTER = [19.2183, 72.9781]
DEFAULT_ZOOM = 12

THANE_LOCALITIES = {
    "Ghodbunder Road": {"lat": 19.2650, "lon": 72.9650},
    "Kopri": {"lat": 19.1820, "lon": 72.9780},
    "Naupada": {"lat": 19.1920, "lon": 72.9720},
    "Wagle Estate": {"lat": 19.1980, "lon": 72.9520},
    "Majiwada": {"lat": 19.2180, "lon": 72.9820},
    "Vartak Nagar": {"lat": 19.2100, "lon": 72.9620},
    "Kalwa": {"lat": 19.1950, "lon": 72.9980},
    "Mumbra": {"lat": 19.1750, "lon": 73.0200},
    "Diva": {"lat": 19.1880, "lon": 73.0420},
    "Kolshet": {"lat": 19.2320, "lon": 72.9880},
}

# File Paths & Data Directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
SAMPLE_CSV_PATH = os.path.join(DATA_DIR, "sample_reports.csv")
TINYDB_PATH = os.path.join(DATA_DIR, "dumpwatch_db.json")
GEOCODE_CACHE_PATH = os.path.join(DATA_DIR, "geocode_cache.json")
