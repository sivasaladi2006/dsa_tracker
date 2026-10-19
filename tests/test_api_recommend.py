import pytest

from app.services.plan import recommend
from app.services.revision import due_reviews
from app.services.stats import latest_submissions

pytestmark = pytest.mark.integration


def get(client, path, **params):
    return client.get(path, params=params)


def test_default_plan_has_the_expected_shape(client):
    response = get(client, "/recommendations")
    assert response.status_code == 200, response.text
    plan = response.json()
    assert set(plan) == {"focus", "reviews"}
    assert 1 <= len(plan["focus"]) <= 3
    assert len(plan["reviews"]) == 3
    topics = [e["topic"] for e in plan["focus"]]
    assert len(topics) == len(set(topics))
    for entry in plan["focus"]:
        assert entry["why"] and 0 <= entry["score"] <= 1
        assert entry["target_difficulty"] in ("Easy", "Medium", "Hard")
        assert len(entry["new_problems"]) <= 3
        assert all(p["why"] for p in entry["new_problems"])


def test_the_endpoint_returns_what_the_engine_computes(client):
    plan = get(client, "/recommendations").json()
    direct = recommend(3, 3, 3)
    assert [e["topic"] for e in plan["focus"]] == [e["topic"] for e in direct["focus"]]
    assert [r["title"] for r in plan["reviews"]] == [r["title"] for r in direct["reviews"]]


def test_the_known_weak_area_shows_up(client):
    focus = get(client, "/recommendations", focus=5).json()["focus"]
    names = {e["topic"] for e in focus}
    requested = {e["requested_by"] for e in focus if e["requested_by"]}
    assert "Graphs" in names or "Graphs" in requested


def test_parameters_shrink_the_plan(client):
    one = get(client, "/recommendations", focus=1, problems=1, reviews=1).json()
    assert len(one["focus"]) == 1
    assert len(one["focus"][0]["new_problems"]) <= 1
    assert len(one["reviews"]) == 1


def test_zero_reviews_gives_an_empty_review_list(client):
    assert get(client, "/recommendations", reviews=0).json()["reviews"] == []


def test_twenty_reviews_are_available(client):
    assert len(get(client, "/recommendations", reviews=20).json()["reviews"]) == 20


@pytest.mark.parametrize(
    "params",
    [{"focus": 0}, {"focus": 11}, {"problems": 0}, {"problems": 11},
     {"reviews": -1}, {"reviews": 21}, {"focus": "abc"}],
    ids=["focus-0", "focus-11", "problems-0", "problems-11", "reviews-negative", "reviews-21", "focus-text"],
)
def test_bad_parameters_are_rejected(client, params):
    assert get(client, "/recommendations", **params).status_code == 422


def test_due_reviews_match_the_service(client):
    due = get(client, "/reviews/due", limit=100).json()
    expected = due_reviews(latest_submissions(), 100)
    assert [d["title"] for d in due] == [e["title"] for e in expected]


def test_due_reviews_default_and_limit(client):
    assert len(get(client, "/reviews/due").json()) == 10
    assert len(get(client, "/reviews/due", limit=1).json()) == 1


def test_due_reviews_are_ordered_unsolved_first_then_most_overdue(client):
    due = get(client, "/reviews/due", limit=100).json()
    solved_flags = [d["status"] == "Solved" for d in due]
    assert solved_flags == sorted(solved_flags)
    for flag in (False, True):
        overdue = [d["overdue_days"] for d in due if (d["status"] == "Solved") == flag]
        assert overdue == sorted(overdue, reverse=True)


def test_the_most_overdue_unsolved_problem_comes_first(client):
    due = get(client, "/reviews/due").json()
    assert due[0]["title"] == "Maximum Subarray" and due[0]["status"] == "Needs Revision"
    assert set(due[0]) == {"title", "difficulty", "status", "overdue_days", "why"}


def test_the_plan_reviews_are_the_start_of_the_due_list(client):
    plan_reviews = get(client, "/recommendations", reviews=5).json()["reviews"]
    due = get(client, "/reviews/due", limit=5).json()
    assert [r["title"] for r in plan_reviews] == [d["title"] for d in due]


@pytest.mark.parametrize("limit", [0, 101])
def test_due_reviews_reject_bad_limits(client, limit):
    assert get(client, "/reviews/due", limit=limit).status_code == 422
