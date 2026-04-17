from src.minhash import MinHash


SIMILAR_DOC_A = {
    ("document", "similarity"),
    ("similarity", "minhash"),
    ("minhash", "lsh"),
}

SIMILAR_DOC_B = {
    ("document", "similarity"),
    ("similarity", "minhash"),
    ("minhash", "locality"),
}

DIFFERENT_DOC = {
    ("neural", "network"),
    ("deep", "learning"),
    ("transformer", "model"),
}


def test_minhash_is_deterministic_for_same_input():
    mh = MinHash(num_hash=20)
    sig1 = mh.compute_signature(SIMILAR_DOC_A)
    sig2 = mh.compute_signature(SIMILAR_DOC_A)
    assert sig1 == sig2
    assert len(sig1) == 20


def test_minhash_returns_zero_signature_for_empty_input():
    mh = MinHash(num_hash=10)
    assert mh.compute_signature(set()) == [0] * 10


def test_minhash_gives_more_matches_for_more_similar_documents():
    mh = MinHash(num_hash=40)
    sig_a = mh.compute_signature(SIMILAR_DOC_A)
    sig_b = mh.compute_signature(SIMILAR_DOC_B)
    sig_c = mh.compute_signature(DIFFERENT_DOC)

    overlap_ab = sum(1 for x, y in zip(sig_a, sig_b) if x == y)
    overlap_ac = sum(1 for x, y in zip(sig_a, sig_c) if x == y)

    assert overlap_ab > overlap_ac