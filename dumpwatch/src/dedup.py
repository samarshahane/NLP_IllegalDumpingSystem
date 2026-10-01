import math
import os
import sys
import numpy as np
import streamlit as st
from sentence_transformers import SentenceTransformer

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


@st.cache_resource
def get_embedder():
    """Load lightweight SentenceTransformer model."""
    return SentenceTransformer("all-MiniLM-L6-v2")


def embed(text: str) -> list:
    """Generate normalized sentence embedding as a list of floats."""
    model = get_embedder()
    emb = model.encode(text, normalize_embeddings=True)
    return emb.tolist()


def haversine_m(lat1, lon1, lat2, lon2):
    """Compute haversine distance in meters between two lat/lon points."""
    R = 6371000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def find_duplicate(new_embedding: list, new_coords: list, new_time_str: str, existing_reports: list):
    """Vectorized duplicate detection based on cosine similarity, spatial distance, and time window."""
    if not existing_reports or not new_embedding:
        return False, None, 0.0

    valid_existing = [r for r in existing_reports if r.get("semantic_embedding") and r.get("coordinates")]
    if not valid_existing:
        return False, None, 0.0

    new_emb_arr = np.array(new_embedding)
    existing_embs = np.array([r["semantic_embedding"] for r in valid_existing])

    # Cosine similarities (vectors are already normalized)
    similarities = np.dot(existing_embs, new_emb_arr)

    for idx, sim in enumerate(similarities):
        if sim >= config.DEDUP_SIM_THRESHOLD:
            orig = valid_existing[idx]
            orig_coords = orig["coordinates"]
            dist = haversine_m(new_coords[0], new_coords[1], orig_coords[0], orig_coords[1])

            if dist <= config.DEDUP_RADIUS_M:
                return True, orig.get("report_id"), round(float(sim), 4)

    return False, None, 0.0
