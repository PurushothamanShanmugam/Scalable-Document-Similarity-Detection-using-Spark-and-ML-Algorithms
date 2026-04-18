import pytest

from src.lsh import LSH


def test_lsh_groups_identical_signatures_into_same_buckets():
    lsh = LSH(bands=2, rows=2)
    signatures = [
        [1, 2, 3, 4],
        [1, 2, 3, 4],
        [8, 9, 10, 11],
    ]
    buckets = lsh.create_buckets(signatures)

    assert buckets[(0, (1, 2))] == [0, 1]
    assert buckets[(1, (3, 4))] == [0, 1]
    assert buckets[(0, (8, 9))] == [2]


def test_lsh_rejects_short_signature():
    lsh = LSH(bands=2, rows=3)
    with pytest.raises(ValueError):
        lsh.create_buckets([[1, 2, 3, 4, 5]])


def test_lsh_rejects_invalid_band_or_row_values():
    with pytest.raises(ValueError):
        LSH(bands=0, rows=2)
    with pytest.raises(ValueError):
        LSH(bands=2, rows=0)