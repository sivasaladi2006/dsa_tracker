import random

import pytest

from app.algorithms import hashing
from app.algorithms.hashing import HashTable, build_title_index, normalize_title


def test_put_and_get():
    table = HashTable()
    table.put("a", 1)
    table.put("b", 2)
    assert table.get("a") == 1 and table.get("b") == 2
    assert len(table) == 2


def test_missing_key_returns_none_or_the_default():
    table = HashTable()
    assert table.get("nope") is None
    assert table.get("nope", -1) == -1


def test_updating_a_key_does_not_grow_the_table():
    table = HashTable()
    table.put("a", 1)
    table.put("a", 2)
    assert table.get("a") == 2
    assert len(table) == 1


def test_delete_existing_and_missing_keys():
    table = HashTable()
    table.put("a", 1)
    assert table.delete("a") is True
    assert table.delete("a") is False
    assert len(table) == 0
    assert "a" not in table


def test_item_syntax_and_membership():
    table = HashTable()
    table["a"] = 1
    assert table["a"] == 1
    assert "a" in table and "b" not in table
    with pytest.raises(KeyError):
        table["b"]


def test_resize_keeps_every_key_and_the_load_factor_low():
    table = HashTable()
    for i in range(1000):
        table.put(f"key{i}", i)
    assert len(table) == 1000
    assert table.bucket_count > 8
    assert table.load_factor() <= 0.75
    assert all(table.get(f"key{i}") == i for i in range(1000))


def test_chaining_survives_total_collisions(monkeypatch):
    monkeypatch.setattr(hashing, "_hash_key", lambda key: 0)  # every key lands in one bucket
    table = HashTable()
    for i in range(20):
        table.put(f"k{i}", i)
    assert len(table) == 20
    assert all(table.get(f"k{i}") == i for i in range(20))
    assert table.delete("k7") is True
    assert table.get("k7") is None and table.get("k8") == 8
    assert len(table) == 19


def test_non_string_keys():
    table = HashTable()
    table.put(1, "one")
    table.put((1, 2), "pair")
    table.put(2.5, "float")
    assert table.get(1) == "one"
    assert table.get((1, 2)) == "pair"
    assert table.get(2.5) == "float"


def test_a_stored_none_counts_as_present():
    table = HashTable()
    table.put("k", None)
    assert "k" in table
    assert len(table) == 1


def test_items_yields_every_pair():
    table = HashTable()
    pairs = {f"k{i}": i for i in range(50)}
    for key, value in pairs.items():
        table.put(key, value)
    assert dict(table.items()) == pairs


def test_string_hash_is_deterministic():
    assert hashing._hash_string("") == 5381
    assert hashing._hash_string("abc") == 193485963  # djb2, worked out by hand


@pytest.mark.parametrize(
    "raw, expected",
    [("  two   SUM ", "two sum"), ("Two Sum", "two sum"), ("a\tb\nc", "a b c")],
)
def test_normalize_title(raw, expected):
    assert normalize_title(raw) == expected


def test_title_index_lookup_ignores_case_and_spacing():
    index = build_title_index([{"title": "Two Sum"}, {"title": "Valid Anagram"}])
    assert index.get(normalize_title("  two   SUM ")) == {"title": "Two Sum"}
    assert index.get(normalize_title("not here")) is None
    assert len(index) == 2


def test_matches_a_dict_under_random_operations():
    rng = random.Random(5)
    for _ in range(50):
        table, reference = HashTable(), {}
        for _step in range(300):
            op = rng.choice(["put", "put", "get", "delete"])
            key = f"k{rng.randint(0, 60)}"
            if op == "put":
                value = rng.randint(0, 1000)
                table.put(key, value)
                reference[key] = value
            elif op == "get":
                assert table.get(key) == reference.get(key)
            else:
                assert table.delete(key) == (key in reference)
                reference.pop(key, None)
            assert len(table) == len(reference)
        assert dict(table.items()) == reference
