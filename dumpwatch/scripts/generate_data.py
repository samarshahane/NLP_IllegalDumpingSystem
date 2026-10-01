import os
import random
import sys
from datetime import datetime, timedelta
import pandas as pd

# Add parent directory to path to allow importing config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

SOURCES = ["citizen", "twitter", "email", "form"]
SEVERITIES = [1, 2, 3, 4, 5]

HOTSPOT_LOCALITIES = ["Wagle Estate", "Ghodbunder Road", "Mumbra", "Kopri"]
OTHER_LOCALITIES = ["Naupada", "Majiwada", "Vartak Nagar", "Kalwa", "Diva", "Kolshet"]

DUMPING_TEMPLATES = [
    "Huge pile of {waste} dumped near {loc} station. Smelling horrible.",
    "People are throwing {waste} right on the side of {loc} road.",
    "Illegal dumping of {waste} noticed behind {loc} market area.",
    "Urgent action needed! Lots of {waste} accumulating in {loc}.",
    "Bohot sara garbage aur {waste} fela hua hai near {loc} bridge.",
    "Chemical & {waste} openly dumped near school in {loc}.",
    "Severe heap of {waste} blocking footpaths in {loc} nagar.",
    "Continuous open burning and dumping of {waste} near {loc} drain.",
]

UNRELATED_TEMPLATES = [
    "Water pipeline leaking near {loc} junction since morning.",
    "Streetlights not working on main road in {loc}.",
    "Potholes on the main flyover in {loc} causing heavy traffic.",
    "Low water pressure in residential area of {loc}.",
    "Bus stop roof broken in {loc}, please fix soon.",
]


def generate_synthetic_reports(num_reports=600):
    """Generate synthetic reports dataset for Thane localities."""
    reports = []
    end_date = datetime.now()
    start_date = end_date - timedelta(days=120)

    # 1. Main reports generation (~560 base reports)
    base_count = num_reports - 40
    for i in range(1, base_count + 1):
        is_dumping = random.random() < 0.75

        # Pick locality (bias towards hotspots)
        if random.random() < 0.60:
            loc_name = random.choice(HOTSPOT_LOCALITIES)
        else:
            loc_name = random.choice(OTHER_LOCALITIES)

        base_coords = config.THANE_LOCALITIES[loc_name]
        # Jitter coordinates slightly
        lat = round(base_coords["lat"] + random.uniform(-0.005, 0.005), 5)
        lon = round(base_coords["lon"] + random.uniform(-0.005, 0.005), 5)

        waste = random.choice(config.WASTE_TYPES)

        if is_dumping:
            template = random.choice(DUMPING_TEMPLATES)
            raw_text = template.format(waste=waste, loc=loc_name)
            severity = random.choice([3, 4, 5]) if waste in ["medical waste", "industrial waste"] else random.choice([1, 2, 3, 4])
        else:
            template = random.choice(UNRELATED_TEMPLATES)
            raw_text = template.format(loc=loc_name)
            waste = "none"
            severity = 1

        # Trend bias: slightly more recent timestamps
        weight = random.random() ** 0.6
        ts = start_date + timedelta(seconds=weight * (end_date - start_date).total_seconds())

        reports.append({
            "report_id": f"REP-{i:04d}",
            "raw_text": raw_text,
            "source": random.choice(SOURCES),
            "locality": loc_name,
            "lat": lat,
            "lon": lon,
            "waste_type": waste,
            "severity": severity,
            "timestamp": ts.strftime("%Y-%m-%d %H:%M:%S"),
            "has_image": random.random() < 0.35,
            "is_dumping": is_dumping,
        })

    # 2. Add ~40 intentional near-duplicate reports
    for i in range(base_count + 1, num_reports + 1):
        original = random.choice([r for r in reports if r["is_dumping"]])
        loc_name = original["locality"]

        # Near coords & close timestamp (within 2 days)
        lat = round(original["lat"] + random.uniform(-0.001, 0.001), 5)
        lon = round(original["lon"] + random.uniform(-0.001, 0.001), 5)
        orig_ts = datetime.strptime(original["timestamp"], "%Y-%m-%d %H:%M:%S")
        ts = orig_ts + timedelta(hours=random.randint(2, 36))

        dup_text = f"Re-reporting again: {original['waste_type']} still lying near {loc_name} area!"

        reports.append({
            "report_id": f"REP-{i:04d}",
            "raw_text": dup_text,
            "source": random.choice(SOURCES),
            "locality": loc_name,
            "lat": lat,
            "lon": lon,
            "waste_type": original["waste_type"],
            "severity": original["severity"],
            "timestamp": ts.strftime("%Y-%m-%d %H:%M:%S"),
            "has_image": random.random() < 0.4,
            "is_dumping": True,
        })

    df = pd.DataFrame(reports)
    os.makedirs(config.DATA_DIR, exist_ok=True)
    df.to_csv(config.SAMPLE_CSV_PATH, index=False)
    print(f"Generated {len(df)} sample reports at {config.SAMPLE_CSV_PATH}")

if __name__ == "__main__":
    generate_synthetic_reports()
