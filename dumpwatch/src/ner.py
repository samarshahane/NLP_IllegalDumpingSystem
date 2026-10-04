import os
import re
import sys
import spacy

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


def get_nlp_model():
    """Load spaCy model with custom locality EntityRuler."""
    try:
        nlp = spacy.load("en_core_web_sm")
    except OSError:
        try:
            import spacy.cli
            spacy.cli.download("en_core_web_sm")
            nlp = spacy.load("en_core_web_sm")
        except Exception:
            nlp = spacy.blank("en")

    # Add EntityRuler before ner component
    if "entity_ruler" not in nlp.pipe_names:
        ruler = nlp.add_pipe("entity_ruler", before="ner" if "ner" in nlp.pipe_names else None)
        patterns = []
        for loc in config.THANE_LOCALITIES.keys():
            patterns.append({"label": "LOCALITY", "pattern": loc})
            patterns.append({"label": "LOCALITY", "pattern": loc.lower()})
        ruler.add_patterns(patterns)

    return nlp


_nlp = None


def extract_locations(text: str) -> list:
    """Extract and rank location entities from text using spaCy and regex fallback."""
    global _nlp
    if _nlp is None:
        _nlp = get_nlp_model()

    doc = _nlp(text)
    localities = []
    other_ents = []

    for ent in doc.ents:
        if ent.label_ == "LOCALITY":
            localities.append(ent.text)
        elif ent.label_ in ["GPE", "LOC", "FAC"]:
            other_ents.append(ent.text)

    # Regex landmark heuristics (e.g. near X station, behind Y mall, Z road, Z nagar)
    landmark_matches = re.findall(
        r"\b(?:near|behind|opposite|at|on)?\s*([A-Z][a-zA-Z0-9\s]+(?:station|road|nagar|naka|bridge|flyover|hospital|market|mall))\b",
        text,
        re.IGNORECASE,
    )

    combined = localities + landmark_matches + other_ents

    # Remove duplicates preserving order
    unique_locations = []
    seen = set()
    for loc in combined:
        cleaned_loc = loc.strip()
        if cleaned_loc.lower() not in seen and len(cleaned_loc) > 2:
            seen.add(cleaned_loc.lower())
            unique_locations.append(cleaned_loc)

    # Fallback to config localities check if empty
    if not unique_locations:
        for loc in config.THANE_LOCALITIES.keys():
            if loc.lower() in text.lower():
                unique_locations.append(loc)

    return unique_locations


if __name__ == "__main__":
    examples = [
        "Huge heap of plastic garbage dumped near Kopri station behind Viviana mall.",
        "Waste dumped openly on Ghodbunder Road near Majiwada flyover.",
        "Garbage pile near Wagle Estate school gate.",
    ]
    for ex in examples:
        print(f"Text: {ex}")
        print(f"Locations: {extract_locations(ex)}\n")
