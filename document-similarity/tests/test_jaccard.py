from src.jaccard import jaccard


def test_jaccard_identical_sets_is_one():
    a = {("document", "similarity"), ("minhash", "lsh")}
    b = {("document", "similarity"), ("minhash", "lsh")}
    assert jaccard(a, b) == 1.0


def test_jaccard_partial_overlap_matches_expected_ratio():
    a = {("document", "similarity"), ("similarity", "minhash")}
    b = {("document", "similarity"), ("minhash", "lsh")}
    assert jaccard(a, b) == 1 / 3


def test_jaccard_empty_sets_are_handled():
    assert jaccard(set(), set()) == 1.0
    assert jaccard({("a", "b")}, set()) == 0.0