import copy

import pytest

from app.schemas import Plan
from app.services.plan import build_plan, render_plan, review_entries


def make_stats(topic, attempted, solved, avg_attempts, days, coverage, total):
    return {"topic": topic, "attempted": attempted, "solved": solved,
            "avg_attempts": avg_attempts, "days_since_last": days,
            "coverage_pct": coverage, "total_problems": total}


STATS = [
    make_stats("A", 10, 10, 1.0, 1, 100, 10),   # score about 0.05: mastered
    make_stats("B", 8, 4, 2.0, 22, 80, 10),     # about 0.49
    make_stats("C", 4, 1, 2.6, 35, 80, 5),      # about 0.66
    make_stats("D", 5, 3, 1.8, 10, 50, 10),     # about 0.40
]
PREREQS = {"C": ["B"], "B": ["A"]}
UNTOUCHED = [
    {"problem_id": 1, "title": "B-Easy", "difficulty": "Easy", "topics": "B"},
    {"problem_id": 2, "title": "B-Medium", "difficulty": "Medium", "topics": "B"},
    {"problem_id": 3, "title": "C-Medium", "difficulty": "Medium", "topics": "B|C"},
    {"problem_id": 4, "title": "D-Hard", "difficulty": "Hard", "topics": "D"},
    {"problem_id": 5, "title": "D-Medium", "difficulty": "Medium", "topics": "D"},
]


def make_latest(pid, title, status, attempts, days_ago):
    return {"problem_id": pid, "title": title, "difficulty": "Medium", "status": status,
            "attempts": attempts, "days_ago": days_ago, "topics": "T"}


LATEST = [
    make_latest(10, "R-Old", "Needs Revision", 2, 13),   # interval 3, overdue 10
    make_latest(11, "R-Solved", "Solved", 1, 40),        # interval 30, overdue 10
    make_latest(12, "R-NotDue", "Solved", 1, 5),         # not due
    make_latest(13, "R-Attempted", "Attempted", 4, 4),   # interval 2, overdue 2
]


@pytest.fixture
def plan():
    return build_plan(STATS, PREREQS, UNTOUCHED, LATEST,
                      focus_count=3, problems_per_topic=2, review_count=3)


def test_focus_topics_are_redirected_deduplicated_and_skip_mastered_ones(plan):
    # C is redirected to B, so B is not listed twice; A is mastered.
    assert [f["topic"] for f in plan["focus"]] == ["B", "D"]
    b, d = plan["focus"]
    assert b["requested_by"] == "C"
    assert d["requested_by"] is None


def test_focus_explanations(plan):
    b, d = plan["focus"]
    assert b["why"].startswith("C ranks higher, but it depends on B (path: C -> B), so start here.")
    assert "you solved 4 of 8 problems tried (50%)" in b["why"]
    assert ("D (score 0.402): you solved 3 of 5 problems tried (60%) and it takes about "
            "1.8 attempts per problem.") in d["why"]


def test_new_problems_for_each_focus_topic(plan):
    b, d = plan["focus"]
    assert b["target_difficulty"] == "Medium" and d["target_difficulty"] == "Medium"
    # C-Medium also covers C, the topic that asked for the redirect, so it leads.
    assert [p["title"] for p in b["new_problems"]] == ["C-Medium", "B-Medium"]
    assert [p["title"] for p in d["new_problems"]] == ["D-Medium", "D-Hard"]
    assert "It also covers C, so it advances both." in b["new_problems"][0]["why"]


def test_reviews_unsolved_first_and_not_due_excluded(plan):
    assert [r["title"] for r in plan["reviews"]] == ["R-Old", "R-Attempted", "R-Solved"]
    assert plan["reviews"][0]["overdue_days"] == 10


def test_limits_are_respected():
    small = build_plan(STATS, PREREQS, UNTOUCHED, LATEST,
                       focus_count=1, problems_per_topic=1, review_count=1)
    assert [f["topic"] for f in small["focus"]] == ["B"]
    assert [p["title"] for p in small["focus"][0]["new_problems"]] == ["C-Medium"]
    assert [r["title"] for r in small["reviews"]] == ["R-Old"]


def test_no_data_gives_an_empty_plan():
    assert build_plan([], {}, [], []) == {"focus": [], "reviews": []}


def test_everything_mastered_renders_helpful_messages():
    mastered_only = build_plan([STATS[0]], {}, [], [])
    assert mastered_only["focus"] == []
    text = render_plan(mastered_only)
    assert "Nothing to focus on" in text
    assert "Nothing due for review." in text


def test_render_plan(plan):
    text = render_plan(plan)
    assert text.startswith("FOCUS TOPICS\n1. C ranks higher")
    assert "   New problems:\n   - C-Medium: new Medium problem in B;" in text
    assert "\n2. D (score 0.402)" in text
    assert ("\n\nREVIEWS DUE\n- R-Old: last result was Needs Revision after 2 attempts, "
            "13 days ago;") in text


def test_render_says_when_no_untouched_problems_are_left():
    text = render_plan(build_plan(STATS, PREREQS, [], LATEST))
    assert "No untouched problems left in this topic; see reviews." in text


def test_review_entries_have_the_api_shape():
    out = review_entries(LATEST, 2)
    assert [r["title"] for r in out] == ["R-Old", "R-Attempted"]
    assert set(out[0]) == {"title", "difficulty", "status", "overdue_days", "why"}
    assert [r["overdue_days"] for r in out] == [10, 2]


def test_plan_fits_the_api_response_model(plan):
    validated = Plan(**plan)
    assert [f.topic for f in validated.focus] == ["B", "D"]
    assert len(validated.reviews) == 3


def test_building_a_plan_does_not_modify_its_inputs():
    before = copy.deepcopy((STATS, PREREQS, UNTOUCHED, LATEST))
    build_plan(STATS, PREREQS, UNTOUCHED, LATEST)
    assert (STATS, PREREQS, UNTOUCHED, LATEST) == before
