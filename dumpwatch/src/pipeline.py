import os
import sys
import uuid
from datetime import datetime
from PIL import Image

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from src.classifier import classify_report
from src.dedup import embed, find_duplicate
from src.geocode import geocode
from src.ner import extract_locations
from src.preprocess import clean_text
from src.storage import Storage, save_custom_waste_type
from src.vision import check_image


def process_report(
    raw_text: str,
    source: str = "citizen",
    image: Image.Image = None,
    timestamp: str = None,
    forced_loc=None,
    waste_type: str = None,
    severity: int = None,
) -> dict:
    """Run full processing pipeline: clean -> classify -> NER -> geocode -> embed -> dedup -> save to DB & CSV."""
    cleaned, _ = clean_text(raw_text)
    clf_res = classify_report(cleaned)

    is_dumping = clf_res["is_dumping"]
    final_waste_type = waste_type if waste_type else clf_res["waste_type"]
    final_severity = severity if severity is not None else clf_res["severity"]

    # Check custom waste type
    if final_waste_type and final_waste_type not in config.WASTE_TYPES and final_waste_type != "unrelated/none":
        save_custom_waste_type(final_waste_type)

    report_id = f"REP-{uuid.uuid4().hex[:6].upper()}"

    # Handle image saving
    image_path = ""
    vision_res = {"shows_dumping": False, "confidence": 0.0}
    if image is not None:
        try:
            img_dir = os.path.join(config.DATA_DIR, "images")
            os.makedirs(img_dir, exist_ok=True)
            image_path = os.path.join(img_dir, f"{report_id}.jpg")
            image.convert("RGB").save(image_path, "JPEG")
            vision_res = check_image(image)
            if vision_res["shows_dumping"] and severity is None:
                final_severity = min(final_severity + 1, 5)
        except Exception:
            pass

    # All submitted complaints start as Pending — rejection is an admin decision, not automatic
    status = "Pending"
    duplicate_of = None

    # Extraction & Geocoding
    extracted_locs = extract_locations(raw_text)
    location_text = extracted_locs[0] if extracted_locs else config.DEFAULT_CITY

    if forced_loc:
        coords = forced_loc
    else:
        coords = geocode(location_text)

    # Embedding & Deduplication
    emb = embed(cleaned)
    storage = Storage()
    existing_reports = storage.get_all()

    if is_dumping:
        ts_str = timestamp or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        is_dup, orig_id, sim = find_duplicate(emb, coords, ts_str, existing_reports)
        if is_dup:
            status = "Duplicate"
            duplicate_of = orig_id

    ts_final = timestamp or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    doc = {
        "report_id": report_id,
        "raw_text": raw_text,
        "clean_text": cleaned,
        "source": source,
        "timestamp": ts_final,
        "coordinates": coords,
        "location_text": location_text,
        "waste_type": final_waste_type,
        "severity": final_severity,
        "status": status,
        "duplicate_of": duplicate_of,
        "semantic_embedding": emb,
        "has_image": image is not None or bool(image_path),
        "image_path": image_path,
    }

    storage.insert_report(doc)
    return doc
