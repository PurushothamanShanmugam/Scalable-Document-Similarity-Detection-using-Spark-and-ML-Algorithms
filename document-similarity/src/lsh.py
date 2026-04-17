from collections import defaultdict
from typing import DefaultDict, Dict, Iterable, List, Sequence, Tuple


class LSH:
    """Banding-based Locality Sensitive Hashing for MinHash signatures."""

    def __init__(self, bands: int, rows: int):
        if bands <= 0 or rows <= 0:
            raise ValueError("bands and rows must be positive")
        self.bands = bands
        self.rows = rows

    def create_buckets(self, signatures: Sequence[Sequence[int]]) -> Dict[Tuple[int, Tuple[int, ...]], List[int]]:
        buckets: DefaultDict[Tuple[int, Tuple[int, ...]], List[int]] = defaultdict(list)
        for doc_idx, signature in enumerate(signatures):
            expected = self.bands * self.rows
            if len(signature) < expected:
                raise ValueError(
                    f"Signature length {len(signature)} is smaller than bands*rows={expected}."
                )
            for band_idx in range(self.bands):
                start = band_idx * self.rows
                end = start + self.rows
                band = tuple(signature[start:end])
                buckets[(band_idx, band)].append(doc_idx)
        return dict(buckets)
