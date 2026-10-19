from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from app.schemas import SubmissionCreate, TopicStats

OK = {"problem_id": 1, "status": "Solved"}


def test_defaults():
    sub = SubmissionCreate(**OK)
    assert sub.attempts == 1
    assert sub.time_taken_min is None
    assert sub.submitted_at is None
    assert sub.notes is None


@pytest.mark.parametrize(
    "fields",
    [
        {**OK, "status": "Done"},
        {**OK, "problem_id": 0},
        {**OK, "attempts": 0},
        {**OK, "attempts": 51},
        {**OK, "time_taken_min": -1},
        {**OK, "time_taken_min": 1441},
        {**OK, "attemps": 2},
        {**OK, "notes": "x" * 501},
        {"problem_id": 1},
        {"status": "Solved"},
    ],
    ids=["bad-status", "problem-id-zero", "attempts-zero", "attempts-51", "negative-time",
         "time-over-a-day", "unknown-field", "notes-too-long", "missing-status", "missing-problem-id"],
)
def test_bad_input_is_rejected(fields):
    with pytest.raises(ValidationError):
        SubmissionCreate(**fields)


@pytest.mark.parametrize(
    "overrides",
    [
        {"attempts": 1},
        {"attempts": 50},
        {"time_taken_min": 0},
        {"time_taken_min": 1440},
        {"notes": "x" * 500},
        {"status": "Attempted"},
        {"status": "Needs Revision"},
    ],
    ids=["attempts-1", "attempts-50", "time-0", "time-1440", "notes-500", "attempted", "needs-revision"],
)
def test_values_at_the_edges_are_accepted(overrides):
    SubmissionCreate(**{**OK, **overrides})


def test_notes_are_trimmed():
    assert SubmissionCreate(**OK, notes="  hi  ").notes == "hi"


def test_blank_notes_become_none():
    assert SubmissionCreate(**OK, notes="   ").notes is None


def test_a_past_date_is_accepted():
    SubmissionCreate(**OK, submitted_at=datetime.now() - timedelta(days=5))


def test_a_future_date_is_rejected():
    with pytest.raises(ValidationError):
        SubmissionCreate(**OK, submitted_at=datetime.now() + timedelta(days=5))


def test_a_date_inside_the_one_day_allowance_is_accepted():
    SubmissionCreate(**OK, submitted_at=datetime.now() + timedelta(hours=23))


def test_a_timezone_aware_date_is_rejected():
    with pytest.raises(ValidationError):
        SubmissionCreate(**OK, submitted_at=datetime.now(timezone.utc))


def test_a_text_timestamp_is_parsed():
    parsed = SubmissionCreate(**OK, submitted_at="2026-10-10T12:30:00").submitted_at
    assert (parsed.year, parsed.month, parsed.day, parsed.hour, parsed.minute) == (2026, 10, 10, 12, 30)


def test_a_topic_with_no_submissions_is_a_valid_response():
    row = TopicStats(topic_id=1, topic="Heaps", total_problems=7, attempted=0, solved=0)
    assert row.solve_pct is None and row.days_since_last is None


def test_explicit_nulls_behave_like_omitted_fields():
    sub = SubmissionCreate(**OK, submitted_at=None, notes=None, time_taken_min=None)
    assert sub.submitted_at is None and sub.notes is None and sub.time_taken_min is None
