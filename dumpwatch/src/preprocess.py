import re

def sanitize_string(s: str) -> str:
    """Remove control characters that can corrupt JSON files."""
    if not isinstance(s, str):
        return str(s)
    return re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', s)


def clean_text(text: str):
    """Remove URLs, emojis, @mentions, extra whitespace; keep hashtags and return (cleaned, original)."""
    if not text:
        return "", ""
    original = sanitize_string(str(text))

    # Remove URLs
    cleaned = re.sub(r"https?://\S+|www\.\S+", "", original)
    # Remove @mentions
    cleaned = re.sub(r"@\w+", "", cleaned)
    # Convert hashtags: #Kopri -> Kopri
    cleaned = re.sub(r"#(\w+)", r"\1", cleaned)
    # Remove non-ASCII/emojis
    cleaned = cleaned.encode("ascii", "ignore").decode("utf-8")
    # Clean up whitespace
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    return cleaned, original


if __name__ == "__main__":
    examples = [
        "Huge heap of #plastic garbage dumped @Kopri station near drain! https://example.com 😷🗑️",
        "Pothole issue on Ghodbunder road near #Naupada bridge. @MuncipalCorp",
        "Chemical leakage and waste open burning near Kopri hospital! #ThaneDump",
    ]
    for ex in examples:
        c, o = clean_text(ex)
        print(f"Original: {o}\nCleaned : {c}\n")
