import random

import pytest

from app.algorithms.sorting import merge_sort

ROWS = [("b", 2), ("a", 1), ("c", 2), ("d", 1)]


def test_sorts_numbers():
    assert merge_sort([5, 2, 9, 1, 5, 6]) == [1, 2, 5, 5, 6, 9]


def test_reverse_order():
    assert merge_sort([5, 2, 9, 1, 5, 6], reverse=True) == [9, 6, 5, 5, 2, 1]


@pytest.mark.parametrize("data", [[], [1], [2, 2, 2], [1, 2, 3], [3, 2, 1]])
def test_simple_cases_match_sorted(data):
    assert merge_sort(data) == sorted(data)
    assert merge_sort(data, reverse=True) == sorted(data, reverse=True)


def test_does_not_modify_the_input():
    data = [3, 1, 2]
    result = merge_sort(data)
    assert data == [3, 1, 2]
    assert result is not data


def test_equal_keys_keep_their_order_ascending():
    assert merge_sort(ROWS, key=lambda r: r[1]) == [("a", 1), ("d", 1), ("b", 2), ("c", 2)]


def test_equal_keys_keep_their_order_descending():
    assert merge_sort(ROWS, key=lambda r: r[1], reverse=True) == [
        ("b", 2), ("c", 2), ("a", 1), ("d", 1)
    ]


def test_multi_field_key():
    items = [(1, "a"), (2, "a"), (1, "b"), (2, "b")]
    # letter ascending, then number descending
    assert merge_sort(items, key=lambda r: (r[1], -r[0])) == [
        (2, "a"), (1, "a"), (2, "b"), (1, "b")
    ]


def test_sort_by_negated_key_gives_descending_order():
    assert merge_sort([3, 1, 2], key=lambda x: -x) == [3, 2, 1]


def test_strings():
    assert merge_sort(["pear", "apple", "fig"]) == ["apple", "fig", "pear"]


def test_matches_sorted_on_random_input_with_many_ties():
    rng = random.Random(3)
    for _ in range(300):
        n = rng.randint(0, 40)
        rows = [(rng.randint(0, 5), rng.randint(0, 5), k) for k in range(n)]
        for key in (lambda r: r[0], lambda r: (r[0], -r[1])):
            for reverse in (False, True):
                assert merge_sort(rows, key=key, reverse=reverse) == sorted(
                    rows, key=key, reverse=reverse
                )
