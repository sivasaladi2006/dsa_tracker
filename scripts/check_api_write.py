from datetime import datetime, timedelta

from fastapi.testclient import TestClient

from app.db import get_connection
from app.main import app

client = TestClient(app)


def count_submissions():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS n FROM submissions")
            return cur.fetchone()["n"]
    finally:
        conn.close()


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


def titles(**params):
    params["limit"] = 100
    return [p["title"] for p in client.get("/problems", params=params).json()["items"]]


assert count_submissions() == 72, "Expected the original 72 sample submissions before testing"
created = []
try:
    assert titles(topic="graphs", status="Untouched") == ["Rotting Oranges"]
    pid = client.get("/problems", params={"topic": "graphs", "status": "Untouched"}).json()["items"][0]["problem_id"]

    # 1. An older, failed attempt with an explicit date, and padded notes
    older = (datetime.now() - timedelta(days=3)).replace(microsecond=0)
    r = client.post("/submissions", json={
        "problem_id": pid, "status": "Attempted", "attempts": 3, "time_taken_min": 50,
        "submitted_at": older.isoformat(), "notes": "  stuck on the BFS queue  ",
    })
    assert r.status_code == 201, r.text
    first = r.json()
    created.append(first["submission_id"])
    assert first["title"] == "Rotting Oranges" and first["problem_id"] == pid
    assert (first["status"], first["attempts"], first["time_taken_min"]) == ("Attempted", 3, 50)
    assert first["notes"] == "stuck on the BFS queue"
    assert first["submitted_at"] == older.isoformat()

    # The problem is no longer untouched, and its latest status is Attempted
    assert titles(topic="graphs", status="Untouched") == []
    assert "Rotting Oranges" in titles(topic="graphs", status="Attempted")

    # 2. A newer successful attempt with defaults filled in
    r = client.post("/submissions", json={"problem_id": pid, "status": "Solved", "attempts": 1, "time_taken_min": 25})
    assert r.status_code == 201, r.text
    second = r.json()
    created.append(second["submission_id"])
    assert second["notes"] is None and second["time_taken_min"] == 25
    stamp = datetime.fromisoformat(second["submitted_at"])
    assert abs((datetime.now() - stamp).total_seconds()) < 120

    # Latest status follows the newest submission, so Rotting Oranges is now Solved
    assert "Rotting Oranges" in titles(topic="graphs", status="Solved")
    assert "Rotting Oranges" not in titles(topic="graphs", status="Attempted")

    # 3. Recent list: newest first
    recent = client.get("/submissions", params={"limit": 2}).json()
    assert [x["submission_id"] for x in recent] == [second["submission_id"], first["submission_id"]]
    assert all(x["title"] == "Rotting Oranges" for x in recent)
    assert len(client.get("/submissions").json()) == 10
    assert client.get("/submissions", params={"limit": 0}).status_code == 422
    assert client.get("/submissions", params={"limit": 101}).status_code == 422

    # 4. Bad requests are rejected and write nothing
    good = {"problem_id": pid, "status": "Solved"}
    assert client.post("/submissions", json={**good, "problem_id": 999999}).status_code == 404
    assert client.post("/submissions", json={**good, "status": "Done"}).status_code == 422
    assert client.post("/submissions", json={**good, "attempts": 0}).status_code == 422
    assert client.post("/submissions", json={**good, "attemps": 2}).status_code == 422
    assert client.post("/submissions", json={"problem_id": pid}).status_code == 422
    future = (datetime.now() + timedelta(days=5)).isoformat()
    assert client.post("/submissions", json={**good, "submitted_at": future}).status_code == 422
    assert client.post("/submissions", json={**good, "submitted_at": "2026-10-10T12:00:00+05:30"}).status_code == 422
    assert count_submissions() == 72 + 2, "A rejected request must not insert a row"
finally:
    delete_submissions(created)

assert count_submissions() == 72
assert titles(topic="graphs", status="Untouched") == ["Rotting Oranges"]
print("Write-endpoint checks passed (test rows removed, database back to 72 submissions)")
