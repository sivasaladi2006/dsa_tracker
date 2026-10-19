import sys

import httpx

from app.db import get_connection

BASE = "http://127.0.0.1:8000"
TITLES = ["Rotting Oranges", "Binary Tree Level Order Traversal", "Implement Queue using Stacks"]
client = httpx.Client(base_url=BASE, timeout=10)


def get(path, **params):
    r = client.get(path, params=params)
    assert r.status_code == 200, (path, r.status_code, r.text)
    return r.json()


def focus_list(plan):
    return [(e["topic"], e["requested_by"]) for e in plan["focus"]]


def show(focus):
    return ", ".join(f"{t} (via {r})" if r else t for t, r in focus)


def stats_by_topic():
    return {r["topic"]: r for r in get("/topics/stats")}


def delete_submissions(ids):
    if not ids:
        return
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.executemany("DELETE FROM submissions WHERE submission_id = %s", [(i,) for i in ids])
        conn.commit()
    finally:
        conn.close()


try:
    health = get("/health")
except httpx.ConnectError:
    sys.exit(f"Server not reachable at {BASE}. Start it in another terminal: uvicorn app.main:app --reload")
assert health["submissions"] == 72, "Expected the original 72 sample submissions before testing"

created = []
try:
    # Baseline
    base_stats = stats_by_topic()
    base_plan = get("/recommendations", focus=5, problems=3, reviews=3)
    base_focus = focus_list(base_plan)
    assert get("/problems", status="Untouched", limit=100)["total"] == 13
    assert base_stats["Stacks & Queues"]["attempted"] == 4
    assert ("Stacks & Queues", "Graphs") in base_focus, base_focus
    items = get("/problems", topic="Stacks & Queues", status="Untouched", limit=100)["items"]
    assert sorted(p["title"] for p in items) == sorted(TITLES), items
    print("BEFORE:", show(base_focus))

    # Log the three recommended problems as solved
    for p in items:
        r = client.post("/submissions", json={
            "problem_id": p["problem_id"], "status": "Solved", "attempts": 1, "time_taken_min": 20})
        assert r.status_code == 201, r.text
        created.append(r.json()["submission_id"])
    assert {x["submission_id"] for x in get("/submissions", limit=3)} == set(created)

    # The data changed
    after_stats = stats_by_topic()
    sq = after_stats["Stacks & Queues"]
    assert (sq["attempted"], sq["solved"], sq["coverage_pct"], sq["days_since_last"]) == (7, 5, 100, 0), sq
    gr = after_stats["Graphs"]
    assert (gr["attempted"], gr["solved"]) == (5, 2), gr        # Rotting Oranges counts for Graphs too
    assert get("/problems", topic="Stacks & Queues", status="Untouched")["total"] == 0
    assert get("/problems", status="Untouched", limit=100)["total"] == 10

    # The plan changed
    after_plan = get("/recommendations", focus=5, problems=3, reviews=3)
    after_focus = focus_list(after_plan)
    new_titles = {p["title"] for e in after_plan["focus"] for p in e["new_problems"]}
    assert not new_titles & set(TITLES), new_titles              # solved problems are not suggested again
    assert ("Stacks & Queues", "Graphs") not in after_focus, after_focus
    assert after_focus != base_focus
    print("AFTER: ", show(after_focus))
    print()
    print("Top recommendation now:", after_plan["focus"][0]["why"])
finally:
    delete_submissions(created)

# Everything is restored
assert get("/health")["submissions"] == 72
assert stats_by_topic()["Stacks & Queues"]["attempted"] == 4
assert focus_list(get("/recommendations", focus=5, problems=3, reviews=3)) == base_focus
print()
print("End-to-end checks passed (test rows removed, database back to 72 submissions)")
