from typing import AbstractSet, Any


def jaccard(a: AbstractSet[Any], b: AbstractSet[Any]) -> float:
    """Compute Jaccard similarity between two sets."""
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0

    union = a | b
    if not union:
        return 0.0
    return len(a & b) / len(union)
