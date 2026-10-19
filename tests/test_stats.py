from datetime import date
from decimal import Decimal

import pytest

from app.services import stats
from app.services.recommender import focus_topics, load_prereqs, rank_focus_topics


# ---------- no database needed ----------

def test_clean_converts_decimals_to_plain_numbers():
    row = stats._clean({"a": Decimal("3"), "b": Decimal("2.5"), "c": "text", "d": None, "e": 7})
    assert row == {"a": 3, "b": 2.5, "c": "text", "d": None, "e": 7}
    assert type(row["a"]) is int and type(row["b"]) is float


def test_weekly_activity_fills_idle_weeks_with_zeros(monkeypatch):
    rows = [
        {"week_start": date(2026, 1, 5), "submissions": 2, "solved": 1, "avg_min": 30},
        {"week_start": date(2026, 1, 19), "submissions": 4, "solved": 3, "avg_min": 40},
    ]
    monkeypatch.setattr(stats, "_fetch", lambda sql: rows)
    weeks = stats.weekly_activity()
    assert [w["week_start"] for w in weeks] == [date(2026, 1, 5), date(2026, 1, 12), date(2026, 1, 19)]
    assert weeks[1] == {"week_start": date(2026, 1, 12), "submissions": 0, "solved": 0, "avg_min": None}
    assert weeks[0]["submissions"] == 2 and weeks[2]["solved"] == 3


def test_weekly_activity_with_no_submissions(monkeypatch):
    monkeypatch.setattr(stats, "_fetch", lambda sql: [])
    assert stats.weekly_activity() == []


def test_activity_summary_with_no_submissions(monkeypatch):
    monkeypatch.setattr(stats, "_fetch", lambda sql: [])
    assert stats.activity_summary() == {}


def test_activity_summary_returns_the_first_row(monkeypatch):
    monkeypatch.setattr(stats, "_fetch", lambda sql: [{"active_days": 3}])
    assert stats.activity_summary() == {"active_days": 3}


# ---------- against the seeded test database ----------

@pytest.mark.integration
def test_weekly_activity_on_the_sample_data(test_database):
    weeks = stats.weekly_activity()
    assert len(weeks) == 14
    assert weeks[0]["week_start"] == date(2026, 7, 13)
    assert sum(w["submissions"] for w in weeks) == 72
    assert sum(w["solved"] for w in weeks) == 43
    assert all(w["submissions"] > 0 for w in weeks)      # no idle weeks in the sample


@pytest.mark.integration
def test_activity_summary_on_the_sample_data(test_database):
    assert stats.activity_summary() == {
        "active_days": 49, "first_day": date(2026, 7, 17),
        "last_day": date(2026, 10, 12), "span_days": 88,
    }


@pytest.mark.integration
def test_revision_queue_on_the_sample_data(test_database):
    queue = stats.revision_queue()
    assert len(queue) == 16
    assert all(r["status"] != "Solved" for r in queue)
    assert queue[0]["title"] == "Maximum Subarray"
    days = [r["days_ago"] for r in queue]
    assert days == sorted(days, reverse=True)


@pytest.mark.integration
def test_untouched_problems_on_the_sample_data(test_database):
    rows = stats.untouched_problems()
    assert len(rows) == 13
    rotting = next(r for r in rows if r["title"] == "Rotting Oranges")
    assert rotting["topics"] == "Graphs|Stacks & Queues"


@pytest.mark.integration
def test_load_prereqs_reads_the_prerequisite_graph(test_database):
    prereqs = load_prereqs()
    assert sum(len(v) for v in prereqs.values()) == 20
    assert sorted(prereqs["Graphs"]) == ["Hashing", "Stacks & Queues", "Trees"]


@pytest.mark.integration
def test_focus_topics_matches_the_ranking_function(test_database):
    direct = rank_focus_topics(stats.topic_stats(), load_prereqs(), 3)
    assert [f["topic"] for f in focus_topics(3)] == [f["topic"] for f in direct]
