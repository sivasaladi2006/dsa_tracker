from datetime import datetime, timedelta

import pytest

pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("restore_submissions")]

FUTURE = (datetime.now() + timedelta(days=5)).isoformat()

BAD_BODIES = {
    "unknown-problem": ({"problem_id": 999999, "status": "Solved"}, 404),
    "bad-status": ({"problem_id": 1, "status": "Done"}, 422),
    "attempts-0": ({"problem_id": 1, "status": "Solved", "attempts": 0}, 422),
    "attempts-51": ({"problem_id": 1, "status": "Solved", "attempts": 51}, 422),
    "negative-time": ({"problem_id": 1, "status": "Solved", "time_taken_min": -1}, 422),
    "time-over-a-day": ({"problem_id": 1, "status": "Solved", "time_taken_min": 1441}, 422),
    "unknown-field": ({"problem_id": 1, "status": "Solved", "attemps": 2}, 422),
    "notes-too-long": ({"problem_id": 1, "status": "Solved", "notes": "x" * 501}, 422),
    "missing-status": ({"problem_id": 1}, 422),
    "missing-problem-id": ({"status": "Solved"}, 422),
    "empty-body": ({}, 422),
    "future-date": ({"problem_id": 1, "status": "Solved", "submitted_at": FUTURE}, 422),
    "timezone-date": ({"problem_id": 1, "status": "Solved",
                       "submitted_at": "2026-10-10T12:00:00+05:30"}, 422),
}


def all_problems(client):
    return client.get("/problems", params={"limit": 100}).json()["items"]


def problem_id(client, title):
    return next(p["problem_id"] for p in all_problems(client) if p["title"] == title)


def latest_status(client, title):
    return next(p["latest_status"] for p in all_problems(client) if p["title"] == title)


def submission_count(client):
    return client.get("/health").json()["submissions"]


def create(client, **body):
    response = client.post("/submissions", json=body)
    assert response.status_code == 201, response.text
    return response.json()


def test_minimal_body_uses_the_defaults(client):
    saved = create(client, problem_id=problem_id(client, "Two Sum"), status="Solved")
    assert saved["title"] == "Two Sum"
    assert (saved["attempts"], saved["time_taken_min"], saved["notes"]) == (1, None, None)
    stamp = datetime.fromisoformat(saved["submitted_at"])
    assert abs((datetime.now() - stamp).total_seconds()) < 120
    assert submission_count(client) == 73


def test_full_body_is_saved_and_notes_are_trimmed(client):
    older = (datetime.now() - timedelta(days=3)).replace(microsecond=0)
    pid = problem_id(client, "Rotting Oranges")
    saved = create(client, problem_id=pid, status="Attempted", attempts=3, time_taken_min=50,
                   submitted_at=older.isoformat(), notes="  stuck on the BFS queue  ")
    assert saved["submission_id"] > 0
    assert saved["problem_id"] == pid and saved["title"] == "Rotting Oranges"
    assert (saved["status"], saved["attempts"], saved["time_taken_min"]) == ("Attempted", 3, 50)
    assert saved["notes"] == "stuck on the BFS queue"
    assert saved["submitted_at"] == older.isoformat()


def test_logging_a_submission_changes_the_latest_status(client):
    pid = problem_id(client, "Rotting Oranges")
    assert latest_status(client, "Rotting Oranges") is None
    older = (datetime.now() - timedelta(days=2)).isoformat()
    create(client, problem_id=pid, status="Attempted", attempts=2, submitted_at=older)
    assert latest_status(client, "Rotting Oranges") == "Attempted"
    create(client, problem_id=pid, status="Solved")
    assert latest_status(client, "Rotting Oranges") == "Solved"


def test_latest_status_follows_submission_time_not_insertion_order(client):
    pid = problem_id(client, "Rotting Oranges")
    create(client, problem_id=pid, status="Solved")
    three_days_ago = (datetime.now() - timedelta(days=3)).isoformat()
    create(client, problem_id=pid, status="Attempted", submitted_at=three_days_ago)
    assert latest_status(client, "Rotting Oranges") == "Solved"


def test_recent_list_is_newest_first(client):
    pid = problem_id(client, "Rotting Oranges")
    older = (datetime.now() - timedelta(days=1)).isoformat()
    first = create(client, problem_id=pid, status="Attempted", submitted_at=older)
    second = create(client, problem_id=pid, status="Solved")
    assert second["submission_id"] != first["submission_id"]
    recent = client.get("/submissions", params={"limit": 2}).json()
    assert [r["submission_id"] for r in recent] == [second["submission_id"], first["submission_id"]]
    assert all(r["title"] == "Rotting Oranges" for r in recent)


def test_default_recent_list_has_ten_entries_in_time_order(client):
    recent = client.get("/submissions").json()
    assert len(recent) == 10
    stamps = [r["submitted_at"] for r in recent]
    assert stamps == sorted(stamps, reverse=True)
    assert set(recent[0]) == {"submission_id", "problem_id", "title", "status", "attempts",
                              "time_taken_min", "submitted_at", "notes"}


def test_recent_list_honours_the_limit(client):
    assert len(client.get("/submissions", params={"limit": 1}).json()) == 1
    assert len(client.get("/submissions", params={"limit": 100}).json()) == 72


@pytest.mark.parametrize("limit", [0, 101])
def test_recent_list_rejects_bad_limits(client, limit):
    assert client.get("/submissions", params={"limit": limit}).status_code == 422


@pytest.mark.parametrize("body, code", list(BAD_BODIES.values()), ids=list(BAD_BODIES))
def test_bad_requests_are_rejected_and_write_nothing(client, body, code):
    assert client.post("/submissions", json=body).status_code == code
    assert submission_count(client) == 72


@pytest.mark.parametrize(
    "overrides",
    [{"attempts": 50}, {"time_taken_min": 0}, {"time_taken_min": 1440}, {"notes": "x" * 500}],
    ids=["attempts-50", "time-0", "time-1440", "notes-500"],
)
def test_values_at_the_edges_are_accepted(client, overrides):
    create(client, problem_id=1, status="Solved", **overrides)


def test_a_date_inside_the_one_day_allowance_is_accepted(client):
    soon = (datetime.now() + timedelta(hours=23)).isoformat()
    create(client, problem_id=1, status="Solved", submitted_at=soon)


def test_explicit_nulls_are_treated_like_omitted_fields(client):
    saved = create(client, problem_id=1, status="Solved",
                   submitted_at=None, notes=None, time_taken_min=None)
    assert saved["notes"] is None and saved["time_taken_min"] is None
    stamp = datetime.fromisoformat(saved["submitted_at"])
    assert abs((datetime.now() - stamp).total_seconds()) < 120
