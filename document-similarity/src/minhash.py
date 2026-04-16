import hashlib
from typing import Iterable, List, Sequence, Tuple


class MinHash:
    """Deterministic MinHash implementation using multiple seeded hashes."""

    def __init__(self, num_hash: int = 50):
        if num_hash <= 0:
            raise ValueError("num_hash must be positive")
        self.num_hash = num_hash
        self.seeds = [f"seed_{i}" for i in range(num_hash)]

    @staticmethod
    def _hash(value: str) -> int:
        return int(hashlib.md5(value.encode("utf-8")).hexdigest(), 16)

    def compute_signature(self, shingles: Sequence[Tuple[str, ...]] | set[Tuple[str, ...]]) -> List[int]:
        if not shingles:
            return [0] * self.num_hash

        signature: List[int] = []
        for seed in self.seeds:
            min_value = None
            for shingle in shingles:
                shingle_text = " ".join(shingle) if isinstance(shingle, tuple) else str(shingle)
                hashed = self._hash(f"{seed}|{shingle_text}")
                if min_value is None or hashed < min_value:
                    min_value = hashed
            signature.append(min_value if min_value is not None else 0)
        return signature
