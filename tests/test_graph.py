import random

import pytest

from app.algorithms.graph import (
    all_prerequisites,
    prerequisite_map,
    topological_sort,
    unmet_prerequisites,
)

EDGES = [
    ("Arrays", "Hashing"), ("Arrays", "Stacks & Queues"), ("Arrays", "Linked Lists"),
    ("Stacks & Queues", "Recursion"), ("Recursion", "Trees"), ("Linked Lists", "Trees"),
    ("Trees", "Graphs"), ("Stacks & Queues", "Graphs"), ("Hashing", "Graphs"),
]
NODES = ["Arrays", "Hashing", "Stacks & Queues", "Linked Lists", "Recursion", "Trees", "Graphs"]
PREREQS = prerequisite_map(EDGES)
DIAMOND = prerequisite_map([("B", "D"), ("C", "D"), ("A", "B"), ("A", "C")])


def test_topological_sort_of_a_chain():
    assert topological_sort(["A", "B", "C"], [("A", "B"), ("B", "C")]) == ["A", "B", "C"]


def test_topological_sort_respects_every_edge():
    order = topological_sort(NODES, EDGES)
    position = {topic: i for i, topic in enumerate(order)}
    assert sorted(order) == sorted(NODES)
    assert all(position[a] < position[b] for a, b in EDGES)


def test_topological_sort_includes_isolated_nodes():
    assert topological_sort(["X", "Y"], []) == ["X", "Y"]


@pytest.mark.parametrize(
    "nodes, edges",
    [
        (["A", "B"], [("A", "B"), ("B", "A")]),
        (["A"], [("A", "A")]),
        (["A", "B", "C"], [("A", "B"), ("B", "C"), ("C", "A")]),
    ],
)
def test_topological_sort_rejects_cycles(nodes, edges):
    with pytest.raises(ValueError, match="Cycle"):
        topological_sort(nodes, edges)


def test_topological_sort_on_random_dags():
    rng = random.Random(11)
    for _ in range(200):
        n = rng.randint(1, 12)
        nodes = [f"T{i}" for i in range(n)]
        edges = [
            (nodes[i], nodes[j])
            for i in range(n)
            for j in range(i + 1, n)
            if rng.random() < 0.25
        ]
        shuffled = nodes[:]
        rng.shuffle(shuffled)
        order = topological_sort(shuffled, edges)
        position = {t: i for i, t in enumerate(order)}
        assert sorted(order) == sorted(nodes)
        assert all(position[a] < position[b] for a, b in edges)


def test_prerequisite_map():
    assert prerequisite_map([("A", "B"), ("C", "B"), ("A", "D")]) == {"B": ["A", "C"], "D": ["A"]}


def test_all_prerequisites_finds_direct_and_indirect_ones():
    found = all_prerequisites("Graphs", PREREQS)
    assert set(found) == {"Arrays", "Hashing", "Stacks & Queues", "Linked Lists", "Recursion", "Trees"}
    assert len(found) == 6
    assert "Graphs" not in found


def test_topics_with_no_prerequisites_or_unknown_topics():
    assert all_prerequisites("Arrays", PREREQS) == []
    assert all_prerequisites("Nope", PREREQS) == []
    assert unmet_prerequisites("Arrays", PREREQS, set()) == []


def test_all_prerequisites_lists_each_topic_once_on_a_diamond():
    found = all_prerequisites("D", DIAMOND)
    assert sorted(found) == ["A", "B", "C"]
    assert len(found) == 3


def test_a_very_deep_chain_does_not_hit_the_recursion_limit():
    nodes = [str(i) for i in range(5000)]
    edges = [(str(i), str(i + 1)) for i in range(4999)]
    assert len(all_prerequisites("4999", prerequisite_map(edges))) == 4999
    assert topological_sort(nodes, edges) == nodes


def test_unmet_prerequisites_come_nearest_first():
    assert unmet_prerequisites("Graphs", PREREQS, set()) == [
        ("Trees", 1), ("Stacks & Queues", 1), ("Hashing", 1),
        ("Recursion", 2), ("Linked Lists", 2), ("Arrays", 2),
    ]


def test_unmet_search_stops_at_mastered_topics():
    assert unmet_prerequisites("Graphs", PREREQS, {"Trees", "Arrays"}) == [
        ("Stacks & Queues", 1), ("Hashing", 1),
    ]


def test_unmet_uses_the_shortest_distance_on_a_diamond():
    assert unmet_prerequisites("D", DIAMOND, set()) == [("B", 1), ("C", 1), ("A", 2)]


def test_nothing_is_unmet_when_everything_is_mastered():
    assert unmet_prerequisites("Graphs", PREREQS, set(NODES)) == []
