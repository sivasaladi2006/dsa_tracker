import random
from bisect import bisect_left, bisect_right

from app.algorithms.graph import (
    all_prerequisites,
    prerequisite_map,
    topological_sort,
    unmet_prerequisites,
)
from app.algorithms.hashing import HashTable
from app.algorithms.search import binary_search, find_in_range, lower_bound, upper_bound
from app.algorithms.sorting import merge_sort

SEED = 7
TRIALS = 500
rng = random.Random(SEED)


def check_search():
    for _ in range(TRIALS):
        data = sorted(rng.randint(0, 15) for _ in range(rng.randint(0, 40)))
        target = rng.randint(-2, 17)
        assert lower_bound(data, target) == bisect_left(data, target), (data, target)
        assert upper_bound(data, target) == bisect_right(data, target), (data, target)

        i = binary_search(data, target)
        if target in data:
            assert i != -1 and data[i] == target, (data, target)
        else:
            assert i == -1, (data, target)

        low = rng.randint(-2, 17)
        high = rng.randint(low, 17)
        assert find_in_range(data, low, high) == [x for x in data if low <= x <= high]

        rows = [{"d": x, "id": k} for k, x in enumerate(data)]
        got = find_in_range(rows, low, high, key=lambda r: r["d"])
        assert got == [r for r in rows if low <= r["d"] <= high]


def check_sorting():
    for _ in range(TRIALS):
        n = rng.randint(0, 40)
        data = [rng.randint(0, 10) for _ in range(n)]
        assert merge_sort(data) == sorted(data), data
        assert merge_sort(data, reverse=True) == sorted(data, reverse=True), data

        # Many ties on purpose: sorted() is stable, so equal keys must stay in input order.
        rows = [(rng.randint(0, 5), rng.randint(0, 5), k) for k in range(n)]
        for key in (lambda r: r[0], lambda r: (r[0], -r[1])):
            for reverse in (False, True):
                assert merge_sort(rows, key=key, reverse=reverse) == sorted(
                    rows, key=key, reverse=reverse
                ), rows

    original = [3, 1, 2]
    merge_sort(original)
    assert original == [3, 1, 2]  # input list must not be modified


def check_hash_table():
    for _ in range(100):
        table, ref = HashTable(), {}
        for _step in range(300):
            op = rng.choice(["put", "put", "get", "delete"])
            key = f"k{rng.randint(0, 60)}"
            if op == "put":
                value = rng.randint(0, 1000)
                table.put(key, value)
                ref[key] = value
            elif op == "get":
                assert table.get(key) == ref.get(key)
            else:
                was_present = key in ref
                assert table.delete(key) == was_present
                ref.pop(key, None)
            assert len(table) == len(ref)
        assert dict(table.items()) == ref


def random_dag(n):
    nodes = [f"T{i}" for i in range(n)]
    edges = [
        (nodes[i], nodes[j])
        for i in range(n)
        for j in range(i + 1, n)
        if rng.random() < 0.25
    ]
    return nodes, edges


def oracle_closure(topic, prereqs):
    seen = set()

    def visit(t):
        for p in prereqs.get(t, []):
            if p not in seen:
                seen.add(p)
                visit(p)

    visit(topic)
    return seen


def oracle_unmet(topic, prereqs, mastered, n):
    """Shortest distances by repeated edge relaxation: a different method from BFS."""
    dist = {topic: 0}
    for _ in range(n + 1):
        for u, d in list(dist.items()):
            if u != topic and u in mastered:
                continue  # do not expand past a mastered topic
            for p in prereqs.get(u, []):
                if p not in dist or d + 1 < dist[p]:
                    dist[p] = d + 1
    return {u: d for u, d in dist.items() if u != topic and u not in mastered}


def check_graph():
    for _ in range(TRIALS):
        n = rng.randint(1, 12)
        nodes, edges = random_dag(n)
        shuffled = nodes[:]
        rng.shuffle(shuffled)

        order = topological_sort(shuffled, edges)
        pos = {t: i for i, t in enumerate(order)}
        assert sorted(order) == sorted(nodes)
        assert all(pos[a] < pos[b] for a, b in edges), (order, edges)

        prereqs = prerequisite_map(edges)
        topic = rng.choice(nodes)
        found = all_prerequisites(topic, prereqs)
        assert len(found) == len(set(found))  # no repeats
        assert set(found) == oracle_closure(topic, prereqs), (topic, edges)

        mastered = {t for t in nodes if rng.random() < 0.3}
        got = unmet_prerequisites(topic, prereqs, mastered)
        assert dict(got) == oracle_unmet(topic, prereqs, mastered, n), (topic, edges, mastered)
        distances = [d for _, d in got]
        assert distances == sorted(distances)  # nearest first

    for _ in range(100):  # every cycle must be rejected
        n = rng.randint(2, 8)
        nodes = [f"T{i}" for i in range(n)]
        edges = [(nodes[i], nodes[i + 1]) for i in range(n - 1)] + [(nodes[-1], nodes[0])]
        try:
            topological_sort(nodes, edges)
        except ValueError:
            continue
        raise AssertionError(f"cycle not detected: {edges}")


if __name__ == "__main__":
    for name, check in [
        ("search", check_search),
        ("sorting", check_sorting),
        ("hash table", check_hash_table),
        ("graph", check_graph),
    ]:
        check()
        print(f"{name}: OK")
    print(f"All algorithm checks passed (seed {SEED}, {TRIALS} trials each)")
