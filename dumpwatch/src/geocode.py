import json
import os
import sys
import time
from geopy.geocoders import Nominatim

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

LAST_REQUEST_TIME = 0.0


def load_cache():
    if os.path.exists(config.GEOCODE_CACHE_PATH):
        try:
            with open(config.GEOCODE_CACHE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_cache(cache):
    os.makedirs(config.DATA_DIR, exist_ok=True)
    try:
        with open(config.GEOCODE_CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(cache, f, indent=2)
    except Exception:
        pass


def geocode(place_text: str):
    """Geocode text query to [lat, lon] using Nominatim with disk cache and rate limiting."""
    global LAST_REQUEST_TIME
    if not place_text:
        return config.DEFAULT_MAP_CENTER

    query = f"{place_text}, {config.DEFAULT_CITY}"
    cache = load_cache()

    if query in cache:
        return cache[query]

    # Check fallback localities in config first before network call
    for loc_name, coords in config.THANE_LOCALITIES.items():
        if loc_name.lower() in place_text.lower():
            res = [coords["lat"], coords["lon"]]
            cache[query] = res
            save_cache(cache)
            return res

    # Rate limiting: ensure at least 1.0 second between Nominatim requests
    now = time.time()
    elapsed = now - LAST_REQUEST_TIME
    if elapsed < 1.0:
        time.sleep(1.0 - elapsed)

    try:
        geolocator = Nominatim(user_agent="dumpwatch-group7")
        LAST_REQUEST_TIME = time.time()
        location = geolocator.geocode(query, timeout=5)
        if location:
            res = [round(location.latitude, 5), round(location.longitude, 5)]
            cache[query] = res
            save_cache(cache)
            return res
    except Exception:
        pass

    # Fallback to default city center
    return config.DEFAULT_MAP_CENTER
