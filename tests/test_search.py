import random
from bisect import bisect_left, bisect_right

import pytest

from app.algorithms.search import binary_search, find_in_range, lower_bound, upper_bound

DATA = [1, 3, 3, 3, 7, 9]


@pytest.mark.parametrize(
    "target, lower, upper",
    [(0, 0, 0), (1, 0, 1), (2, 1, 1), (3, 1, 4), (7, 4, 5), (9, 5, 6), (10, 6, 6)],
)
def test_bounds_on_a_known_list(target, lower, upper):
    assert lower_bound(DATA, target) == lower
    assert upper_bound(DATA, target) == upper


@pytest.mark.parametrize(
    "target, expected", [(1, 0), (7, 4), (9, 5), (0, -1), (4, -1), (10, -1)]
)
def test_binary_search_on_unique_values(target, expected):
    assert binary_search(DATA, target) == expected


def test_binary_search_returns_a_matching_index_when_there_are_duplicates():
    i = binary_search(DATA, 3)
    assert DATA[i] == 3


def test_empty_list():
    assert lower_bound([], 5) == 0
    assert upper_bound([], 5) == 0
    assert binary_search([], 5) == -1
    assert find_in_range([], 0, 10) == []


def test_single_element():
    assert [lower_bound([5], t) for t in (4, 5, 6)] == [0, 0, 1]
    assert [upper_bound([5], t) for t in (4, 5, 6)] == [0, 1, 1]
    assert binary_search([5], 5) == 0


@pytest.mark.parametrize(
    "low, high, expected",
    [(3, 7, [3, 3, 3, 7]), (0, 100, DATA), (-5, 0, []), (10, 20, []), (5, 3, []), (4, 6, [])],
)
def test_find_in_range_on_numbers(low, high, expected):
    assert find_in_range(DATA, low, high) == expected


def test_find_in_range_with_a_key_on_rows():
    rows = [{"d": 5}, {"d": 8}, {"d": 8}, {"d": 12}, {"d": 20}]
    found = find_in_range(rows, 8, 12, key=lambda r: r["d"])
    assert found == [{"d": 8}, {"d": 8}, {"d": 12}]


def test_matches_bisect_on_random_lists():
    rng = random.Random(7)
    for _ in range(300):
        data = sorted(rng.randint(0, 15) for _ in range(rng.randint(0, 40)))
        target = rng.randint(-2, 17)
        assert lower_bound(data, target) == bisect_left(data, target)
        assert upper_bound(data, target) == bisect_right(data, target)
        low = rng.randint(-2, 17)
        high = rng.randint(low, 17)
        assert find_in_range(data, low, high) == [x for x in data if low <= x <= high]
        found = binary_search(data, target)
        assert (found != -1) == (target in data)
        if found != -1:
            assert data[found] == target


def test_searching_does_not_modify_the_list():
    data = list(DATA)
    lower_bound(data, 3)
    upper_bound(data, 3)
    binary_search(data, 3)
    find_in_range(data, 1, 7)
    assert data == DATA
