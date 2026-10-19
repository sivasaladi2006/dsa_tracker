from datetime import datetime, timedelta, timezone

from pydantic import ValidationError

from app.schemas import Plan, SubmissionCreate, TopicStats


def invalid(**fields):
    try:
        SubmissionCreate(**fields)
    except ValidationError:
        return True
    return False


OK = {"problem_id": 1, "status": "Solved"}

# Defaults
sub = SubmissionCreate(**OK)
assert sub.attempts == 1 and sub.time_taken_min is None and sub.submitted_at is None and sub.notes is None

# Each rule rejects bad input...
assert invalid(**{**OK, "status": "Done"})
assert invalid(**{**OK, "problem_id": 0})
assert invalid(**{**OK, "attempts": 0})
assert invalid(**{**OK, "attempts": 51})
assert invalid(**{**OK, "time_taken_min": -1})
assert invalid(**{**OK, "time_taken_min": 1441})
assert invalid(**{**OK, "attemps": 2})                      # typo'd field is rejected
assert invalid(**{**OK, "notes": "x" * 501})
assert invalid(problem_id=1)                                # status is required
assert invalid(status="Solved")                             # problem_id is required

# ...and the edges of each range are accepted
assert not invalid(**{**OK, "attempts": 1})
assert not invalid(**{**OK, "attempts": 50})
assert not invalid(**{**OK, "time_taken_min": 0})
assert not invalid(**{**OK, "time_taken_min": 1440})
assert not invalid(**{**OK, "notes": "x" * 500})
for status in ("Solved", "Attempted", "Needs Revision"):
    assert not invalid(**{**OK, "status": status})

# Notes are trimmed; blank notes become None
assert SubmissionCreate(**OK, notes="  hi  ").notes == "hi"
assert SubmissionCreate(**OK, notes="   ").notes is None

# Dates: past is fine, a text timestamp is parsed, future and timezones are rejected
now = datetime.now()
assert not invalid(**{**OK, "submitted_at": now - timedelta(days=5)})
assert invalid(**{**OK, "submitted_at": now + timedelta(days=5)})
assert invalid(**{**OK, "submitted_at": datetime.now(timezone.utc)})
parsed = SubmissionCreate(**OK, submitted_at="2026-10-10T12:30:00").submitted_at
assert (parsed.year, parsed.month, parsed.day, parsed.hour, parsed.minute) == (2026, 10, 10, 12, 30)

# Responses accept missing optional values (a topic with no submissions)
row = TopicStats(topic_id=1, topic="Heaps", total_problems=7, attempted=0, solved=0)
assert row.solve_pct is None and row.days_since_last is None

print("Schema checks passed")
