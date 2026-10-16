from datetime import timedelta

from app.algorithms.graph import all_prerequisites, prerequisite_map, unmet_prerequisites
from app.algorithms.hashing import build_title_index, normalize_title
from app.algorithms.search import find_in_range
from app.algorithms.sorting import merge_sort
from app.db import get_connection
from app.services.stats import topic_stats


def load(sql):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            return cur.fetchall()
    finally:
        conn.close()


def demo_binary_search():
    print("=== 1. BINARY SEARCH: submissions in the last 14 days of activity ===")
    rows = load(
        "SELECT p.title, s.status, s.submitted_at FROM submissions s "
        "JOIN problems p ON p.problem_id = s.problem_id"
    )
    rows = merge_sort(rows, key=lambda r: r["submitted_at"])  # search needs sorted input
    latest = rows[-1]["submitted_at"]
    low = latest - timedelta(days=14)
    recent = find_in_range(rows, low, latest, key=lambda r: r["submitted_at"])
    assert recent == [r for r in rows if low <= r["submitted_at"] <= latest]
    solved = sum(1 for r in recent if r["status"] == "Solved")
    print(f"Window: {low:%Y-%m-%d} to {latest:%Y-%m-%d}")
    print(f"{len(recent)} of {len(rows)} submissions fall in the window, {solved} solved")
    print("Matches a plain list filter: True\n")


def demo_ranking():
    print("=== 2. MERGE SORT: topics ranked weakest first ===")
    stats = [r for r in topic_stats() if r["attempted"] > 0]

    def weakness(r):
        # lowest solve rate first; ties: more attempts first; then longer since practiced
        return (r["solve_pct"], -r["avg_attempts"], -r["days_since_last"])

    ranked = merge_sort(stats, key=weakness)
    assert ranked == sorted(stats, key=weakness)
    for i, r in enumerate(ranked[:5], start=1):
        print(f"{i}. {r['topic']:<20} solve {r['solve_pct']}%  "
              f"attempts {r['avg_attempts']}  last practiced {r['days_since_last']}d ago")
    print("Matches Python's sorted(): True\n")


def demo_title_index():
    print("=== 3. HASH TABLE: problem lookup by title ===")
    problems = load("SELECT problem_id, title, difficulty FROM problems")
    index = build_title_index(problems)
    print(f"{len(index)} problems indexed in {index.bucket_count} buckets "
          f"(load factor {index.load_factor():.2f})")
    for query in ["  LARGEST rectangle   in histogram ", "two sum", "Not A Real Problem"]:
        hit = index.get(normalize_title(query))
        result = f"{hit['title']} ({hit['difficulty']})" if hit else "not found"
        print(f"  {query!r:<42} -> {result}")
    print()


def demo_prerequisites():
    print("=== 4. DFS / BFS: what to fix before the weakest topic ===")
    edge_rows = load(
        "SELECT p.name AS prereq, t.name AS topic FROM topic_prerequisites tp "
        "JOIN topics t ON t.topic_id = tp.topic_id "
        "JOIN topics p ON p.topic_id = tp.prereq_id"
    )
    prereqs = prerequisite_map([(r["prereq"], r["topic"]) for r in edge_rows])

    stats = [r for r in topic_stats() if r["attempted"] > 0]
    mastered = {r["topic"] for r in stats if r["attempted"] >= 5 and r["solve_pct"] >= 75}
    weakest = merge_sort(stats, key=lambda r: r["solve_pct"])[0]["topic"]

    print(f"Mastered (5+ problems tried, 75%+ solved): {sorted(mastered)}")
    print(f"Weakest topic: {weakest}")
    print(f"DFS, everything {weakest} depends on: {all_prerequisites(weakest, prereqs)}")
    print(f"BFS, gaps to fix first (name, distance): "
          f"{unmet_prerequisites(weakest, prereqs, mastered)}")


if __name__ == "__main__":
    demo_binary_search()
    demo_ranking()
    demo_title_index()
    demo_prerequisites()
