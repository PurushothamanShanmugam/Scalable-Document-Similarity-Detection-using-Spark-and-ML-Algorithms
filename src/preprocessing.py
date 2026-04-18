import re
from typing import List

STOP_WORDS = {
    "a", "an", "the", "and", "or", "but", "if", "while", "with", "of", "at", "by", "for",
    "to", "from", "up", "down", "in", "out", "on", "off", "over", "under", "again", "further",
    "then", "once", "here", "there", "all", "any", "both", "each", "few", "more", "most",
    "other", "some", "such", "no", "nor", "not", "only", "own", "same", "so", "than", "too",
    "very", "can", "will", "just", "is", "am", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "this", "that", "these", "those", "he", "she",
    "it", "they", "them", "his", "her", "its", "their", "we", "you", "your", "yours", "our",
    "ours", "i", "me", "my", "mine", "as", "into", "about", "after", "before", "between",
    "during", "through", "above", "below", "because", "until", "against", "once"
}


def preprocess(doc: str) -> List[str]:
    """Convert a document into cleaned tokens using lightweight local logic."""
    if not isinstance(doc, str):
        raise TypeError("Input document must be a string.")

    doc = doc.lower()
    doc = re.sub(r"[^a-z\s]", " ", doc)
    doc = re.sub(r"\s+", " ", doc).strip()
    if not doc:
        return []

    tokens = doc.split()
    return [token for token in tokens if token not in STOP_WORDS]


if __name__ == "__main__":
    sample = "Machine learning is AMAZING!! and powerful."
    print(preprocess(sample))
