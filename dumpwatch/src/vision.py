import streamlit as st
from PIL import Image


def check_image(pil_image: Image.Image) -> dict:
    """Classify image evidence zero-shot using CLIP, failing gracefully if torchvision/transformers dependencies are missing."""
    if pil_image is None:
        return {"shows_dumping": False, "confidence": 0.0}

    try:
        from transformers import pipeline

        pipe = pipeline("zero-shot-image-classification", model="openai/clip-vit-base-patch32")
        candidate_labels = [
            "a photo of illegally dumped garbage",
            "a clean street",
            "an unrelated photo",
        ]

        res = pipe(pil_image, candidate_labels=candidate_labels)
        top_label = res[0]["label"]
        score = float(res[0]["score"])

        shows_dumping = top_label == "a photo of illegally dumped garbage" and score > 0.4
        return {"shows_dumping": shows_dumping, "confidence": round(score, 4)}
    except Exception:
        # Graceful fallback if torchvision or CLIP dependencies are not installed
        return {"shows_dumping": False, "confidence": 0.0}
