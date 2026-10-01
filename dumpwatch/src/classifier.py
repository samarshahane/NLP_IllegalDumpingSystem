import os
import sys
import streamlit as st
from transformers import pipeline

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


@st.cache_resource
def get_classifier():
    """Load HF zero-shot classification pipeline (cached)."""
    return pipeline(
        "zero-shot-classification",
        model="typeform/distilbert-base-uncased-mnli",
    )


def calculate_severity(text: str, waste_type: str = "") -> int:
    """Rule-based severity estimation (1-5)."""
    score = 2
    text_lower = text.lower()

    high_risk_keywords = ["medical", "hazardous", "chemical", "hospital", "school", "burning", "fire", "river", "drain", "lake"]
    large_quantity_keywords = ["huge", "massive", "truckload", "mountain", "overflowing", "tons"]

    for kw in high_risk_keywords:
        if kw in text_lower:
            score += 1
            break

    for kw in large_quantity_keywords:
        if kw in text_lower:
            score += 1
            break

    if waste_type in ["medical waste", "industrial waste"]:
        score += 1

    return min(max(score, 1), 5)


def classify_report(text: str) -> dict:
    """Classify report text for dumping status, waste type, and severity."""
    try:
        clf = get_classifier()
        res = clf(text, candidate_labels=config.CLASSIFY_LABELS)
        top_label = res["labels"][0]
        confidence = float(res["scores"][0])

        dumping_keywords = ["dump", "garbage", "waste", "trash", "debris", "litter", "rubbish"]
        text_lower = text.lower()
        has_dumping_kw = any(kw in text_lower for kw in dumping_keywords)

        if "dump" in text_lower and top_label in ["illegal waste dumping", "garbage collection complaint"]:
            top_label = "illegal waste dumping"

        is_dumping = (
            (top_label == "illegal waste dumping" and confidence >= 0.35)
            or (has_dumping_kw and top_label in ["illegal waste dumping", "garbage collection complaint"])
        )
        if not is_dumping and has_dumping_kw and top_label != "unrelated" and confidence > 0.3:
            is_dumping = True

        waste_type = "unrelated/none"

        if is_dumping:
            waste_res = clf(text, candidate_labels=config.WASTE_TYPES)
            waste_type = waste_res["labels"][0]

        severity = calculate_severity(text, waste_type) if is_dumping else 1

        return {
            "is_dumping": is_dumping,
            "label": top_label,
            "confidence": round(confidence, 4),
            "waste_type": waste_type,
            "severity": severity,
        }
    except Exception as e:
        return {
            "is_dumping": False,
            "label": "error",
            "confidence": 0.0,
            "waste_type": "none",
            "severity": 1,
            "error": str(e),
        }


def classify_batch(texts: list) -> list:
    """Classify multiple texts."""
    return [classify_report(t) for t in texts]


if __name__ == "__main__":
    examples = [
        "Huge pile of medical waste and syringes dumped openly near Kopri hospital!",
        "Potholes on the main road causing traffic near Wagle Estate.",
        "People throwing household garbage and plastic bags near Ghodbunder road drain.",
    ]
    for ex in examples:
        print(f"Text: {ex}")
        print(f"Result: {classify_report(ex)}\n")
