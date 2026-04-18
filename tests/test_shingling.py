import pytest

from src.shingling import create_shingles


def test_create_shingles_for_project_tokens():
    tokens = ["document", "similarity", "minhash", "lsh"]
    shingles = create_shingles(tokens, k=2)
    assert shingles == {
        ("document", "similarity"),
        ("similarity", "minhash"),
        ("minhash", "lsh"),
    }


def test_create_shingles_returns_single_tuple_when_tokens_shorter_than_k():
    assert create_shingles(["minhash"], k=2) == {("minhash",)}


def test_create_shingles_rejects_invalid_k():
    with pytest.raises(ValueError):
        create_shingles(["a", "b"], k=0)