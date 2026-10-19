from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def get(path, **params):
    return client.get(path, params=params)


# /topics
r = get("/topics")
assert r.status_code == 200
topics = r.json()
assert len(topics) == 16
assert topics[0]["name"] == "Arrays" and topics[-1]["name"] == "Two Pointers"
assert set(topics[0]) == {"topic_id", "name"}

# /topics/stats
rows = get("/topics/stats").json()
assert len(rows) == 16
arrays = next(x for x in rows if x["topic"] == "Arrays")
assert (arrays["total_problems"], arrays["attempted"], arrays["solved"]) == (28, 23, 17)

# /problems: paging
page = get("/problems").json()
assert (page["total"], page["limit"], page["offset"], len(page["items"])) == (72, 50, 0, 50)
first = page["items"][0]
assert first["title"] == "Two Sum" and first["topics"] == ["Arrays", "Hashing"]
assert first["latest_status"] == "Solved"
assert len(get("/problems", offset=50).json()["items"]) == 22
assert len(get("/problems", limit=10, offset=70).json()["items"]) == 2
assert get("/problems", offset=500).json()["items"] == []

# /problems: status filter (latest submission per problem)
counts = {s: get("/problems", status=s).json()["total"]
          for s in ["Solved", "Attempted", "Needs Revision", "Untouched"]}
assert counts == {"Solved": 43, "Attempted": 10, "Needs Revision": 6, "Untouched": 13}, counts
untouched = get("/problems", status="Untouched", limit=100).json()["items"]
assert len(untouched) == 13 and all(p["latest_status"] is None for p in untouched)

# /problems: difficulty filter
by_difficulty = {d: get("/problems", difficulty=d).json()["total"] for d in ["Easy", "Medium", "Hard"]}
assert by_difficulty == {"Easy": 19, "Medium": 42, "Hard": 11}, by_difficulty

# /problems: topic filter is case-insensitive and combines with the others
graphs = get("/problems", topic="graphs").json()
assert graphs["total"] == 5 and all("Graphs" in p["topics"] for p in graphs["items"])
assert [p["title"] for p in get("/problems", topic="Graphs", status="Untouched").json()["items"]] == ["Rotting Oranges"]
assert [p["title"] for p in get("/problems", topic="Dynamic Programming", difficulty="Hard").json()["items"]] == ["Edit Distance"]
assert get("/problems", topic="Heaps", status="Untouched").json() == {
    "total": 0, "limit": 50, "offset": 0, "items": []}   # Heaps is 100% covered

# errors
assert get("/problems", topic="Nope").status_code == 404
assert get("/problems", difficulty="Impossible").status_code == 422
assert get("/problems", status="Done").status_code == 422
assert get("/problems", limit=0).status_code == 422
assert get("/problems", limit=101).status_code == 422
assert get("/problems", offset=-1).status_code == 422

print("Read-endpoint checks passed")
