from fastapi.testclient import TestClient

from app.main import app
from app.services.plan import recommend
from app.services.revision import due_reviews
from app.services.stats import latest_submissions

client = TestClient(app)


def get(path, **params):
    return client.get(path, params=params)


# /recommendations: default shape
r = get("/recommendations")
assert r.status_code == 200, r.text
plan = r.json()
assert set(plan) == {"focus", "reviews"}
assert 1 <= len(plan["focus"]) <= 3
assert len(plan["reviews"]) == 3
for entry in plan["focus"]:
    assert entry["why"] and 0 <= entry["score"] <= 1
    assert entry["target_difficulty"] in ("Easy", "Medium", "Hard")
    assert len(entry["new_problems"]) <= 3
    assert all(p["why"] for p in entry["new_problems"])
topics = [e["topic"] for e in plan["focus"]]
assert len(topics) == len(set(topics))                       # no topic twice

# The endpoint returns exactly what the engine computes
direct = recommend(3, 3, 3)
assert topics == [e["topic"] for e in direct["focus"]]
assert [r["title"] for r in plan["reviews"]] == [r["title"] for r in direct["reviews"]]

# The weak area of the sample data shows up, directly or as a redirect
wide = get("/recommendations", focus=5).json()["focus"]
names = {e["topic"] for e in wide}
requested = {e["requested_by"] for e in wide if e["requested_by"]}
assert "Graphs" in names or "Graphs" in requested, (names, requested)

# Query parameters change the size of the plan
one = get("/recommendations", focus=1, problems=1, reviews=1).json()
assert len(one["focus"]) == 1 and len(one["focus"][0]["new_problems"]) <= 1 and len(one["reviews"]) == 1
assert get("/recommendations", reviews=0).json()["reviews"] == []
assert len(get("/recommendations", reviews=20).json()["reviews"]) == 20

# Bad parameters are rejected
for params in ({"focus": 0}, {"focus": 11}, {"problems": 0}, {"problems": 11},
               {"reviews": -1}, {"reviews": 21}, {"focus": "abc"}):
    assert get("/recommendations", **params).status_code == 422, params

# /reviews/due: matches the service, unsolved first, then most overdue first
due = get("/reviews/due", limit=100).json()
expected = due_reviews(latest_submissions(), 100)
assert [d["title"] for d in due] == [e["title"] for e in expected]
assert len(get("/reviews/due").json()) == 10
assert len(get("/reviews/due", limit=1).json()) == 1
solved_flags = [d["status"] == "Solved" for d in due]
assert solved_flags == sorted(solved_flags)
for flag in (False, True):
    overdue = [d["overdue_days"] for d in due if (d["status"] == "Solved") == flag]
    assert overdue == sorted(overdue, reverse=True)
assert due[0]["status"] != "Solved" and due[0]["title"] == "Maximum Subarray"
assert set(due[0]) == {"title", "difficulty", "status", "overdue_days", "why"}

# The plan's reviews are the first entries of /reviews/due
assert [r["title"] for r in get("/recommendations", reviews=5).json()["reviews"]] == \
       [d["title"] for d in get("/reviews/due", limit=5).json()]

for params in ({"limit": 0}, {"limit": 101}):
    assert get("/reviews/due", **params).status_code == 422, params

print("Recommendation-endpoint checks passed")
