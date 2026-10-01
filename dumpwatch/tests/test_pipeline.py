import os
import sys
import pandas as pd
import pytest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from src.classifier import classify_report
from src.dedup import embed, find_duplicate
from src.hotspot import find_hotspots
from src.ner import extract_locations


def test_classifier_detects_dumping():
    text = "Massive pile of plastic waste and garbage dumped on Ghodbunder Road!"
    res = classify_report(text)
    assert res["is_dumping"] is True
    assert res["label"] == "illegal waste dumping"


def test_classifier_rejects_unrelated():
    text = "Potholes on main flyover near Wagle Estate causing traffic jam."
    res = classify_report(text)
    assert res["is_dumping"] is False


def test_ner_extracts_kopri():
    text = "Huge garbage pile near Kopri station behind market."
    locs = extract_locations(text)
    assert any("kopri" in l.lower() for l in locs)


def test_dedup_flags_near_identical_nearby():
    text1 = "Massive plastic dumping near Kopri station"
    text2 = "Massive plastic waste dumped near Kopri station area"
    emb1 = embed(text1)
    emb2 = embed(text2)

    existing = [{
        "report_id": "REP-001",
        "semantic_embedding": emb1,
        "coordinates": [19.1820, 72.9780],
    }]

    is_dup, orig_id, sim = find_duplicate(emb2, [19.1821, 72.9781], "2026-10-01 10:00:00", existing)
    assert is_dup is True
    assert orig_id == "REP-001"


def test_dedup_does_not_flag_far_away():
    text1 = "Massive plastic dumping near Kopri station"
    text2 = "Massive plastic dumping near Kopri station"
    emb1 = embed(text1)
    emb2 = embed(text2)

    existing = [{
        "report_id": "REP-001",
        "semantic_embedding": emb1,
        "coordinates": [19.1820, 72.9780],
    }]

    # Coords 20km away (Mumbra / Diva)
    is_dup, orig_id, sim = find_duplicate(emb2, [19.3500, 73.1500], "2026-10-01 10:00:00", existing)
    assert is_dup is False


def test_hotspot_returns_cluster():
    # 5 close incidents near Kopri
    reports = [
        {"report_id": f"R{i}", "lat": 19.1820 + (i * 0.0001), "lon": 72.9780 + (i * 0.0001), "severity": 4, "waste_type": "plastic waste", "status": "Pending"}
        for i in range(5)
    ]
    df = pd.DataFrame(reports)
    _, summary = find_hotspots(df)
    assert not summary.empty
    assert len(summary) >= 1
