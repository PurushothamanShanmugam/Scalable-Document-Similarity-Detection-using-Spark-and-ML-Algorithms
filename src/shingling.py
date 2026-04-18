from typing import Iterable, Sequence, Set, Tuple


Shingle = Tuple[str, ...]


def create_shingles(tokens: Sequence[str], k: int = 2) -> Set[Shingle]:
    """Create k-shingles from a token sequence."""
    if k <= 0:
        raise ValueError("Shingle size k must be positive.")

    if not tokens:
        return set()

    if len(tokens) < k:
        return {tuple(tokens)}

    return {tuple(tokens[i : i + k]) for i in range(len(tokens) - k + 1)}
