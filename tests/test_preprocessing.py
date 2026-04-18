import pytest

from src.preprocessing import preprocess


def test_preprocess_lowercases_removes_punctuation_and_stopwords():
    text = "Document similarity with MinHash and LSH detects near-duplicate documents!!!"
    tokens = preprocess(text)
    assert tokens == [
        "document",
        "similarity",
        "minhash",
        "lsh",
        "detects",
        "near",
        "duplicate",
        "documents",
    ]


def test_preprocess_returns_empty_list_for_only_symbols():
    assert preprocess("!!! 123 ###") == []


def test_preprocess_raises_type_error_for_non_string():
    with pytest.raises(TypeError):
        preprocess(["not", "a", "string"])