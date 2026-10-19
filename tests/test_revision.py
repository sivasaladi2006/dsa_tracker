import copy

import pytest

from app.services.revision import due_reviews, review_interval


def row(pid, status, attempts, days_ago):
    return {"problem_id": pid, "title": f"P{pid}", "difficulty": "Medium",
            "status": status, "attempts": attempts, "days_ago": days_ago, "topics": "T"}


def ids(rows):
    return [r["problem_id"] for r in rows]


ROWS = [
    row(1, "Attempted", 3, 5),        # interval 2, overdue 3  -> due
    row(2, "Needs Revision", 2, 3),   # interval 3, overdue 0  -> due
    row(3, "Needs Revision", 2, 2),   # overdue -1             -> not due
    row(4, "Solved", 1, 30),          # interval 30, overdue 0 -> due
    row(5, "Solved", 1, 29),          # overdue -1             -> not due
    row(6, "Solved", 2, 20),          # interval 14, overdue 6 -> due
    row(7, "Solved", 3, 7),           # interval 7, overdue 0  -> due
    row(8, "Solved", 4, 10),          # interval 7, overdue 3  -> due
]


@pytest.mark.parametrize(
    "status, attempts, expected",
    [
        ("Attempted", 5, 2),
        ("Attempted", 1, 2),
        ("Needs Revision", 1, 3),
        ("Needs Revision", 9, 3),
        ("Solved", 0, 30),
        ("Solved", 1, 30),
        ("Solved", 2, 14),
        ("Solved", 3, 7),
        ("Solved", 6, 7),
    ],
)
def test_review_interval(status, attempts, expected):
    assert review_interval(status, attempts) == expected


def test_unsolved_come_first_then_most_overdue():
    out = due_reviews(ROWS, count=10)
    assert ids(out) == [1, 2, 6, 8, 4, 7]
    assert [r["overdue_days"] for r in out] == [3, 0, 6, 3, 0, 0]
    assert [r["interval_days"] for r in out] == [2, 3, 14, 7, 30, 7]


def test_count_limit_and_default_count():
    assert ids(due_reviews(ROWS, count=3)) == [1, 2, 6]
    assert len(due_reviews(ROWS)) == 5      # six are due, the default shows five


def test_nothing_attempted():
    assert due_reviews([]) == []


def test_nothing_due():
    assert due_reviews([row(9, "Solved", 1, 5)]) == []


def test_exactly_at_the_interval_is_due_and_one_day_short_is_not():
    out = due_reviews([row(40, "Solved", 1, 30), row(41, "Solved", 1, 29)])
    assert ids(out) == [40]
    assert out[0]["overdue_days"] == 0


def test_unsolved_ties_break_by_problem_id():
    # Both are 10 days overdue; the input lists the higher id first.
    out = due_reviews([row(21, "Needs Revision", 1, 13), row(20, "Attempted", 1, 12)])
    assert [r["overdue_days"] for r in out] == [10, 10]
    assert ids(out) == [20, 21]


def test_unsolved_outrank_solved_even_when_the_solved_one_is_far_more_overdue():
    out = due_reviews([row(30, "Solved", 1, 100), row(31, "Attempted", 1, 3)])
    assert [r["overdue_days"] for r in out] == [1, 70]
    assert ids(out) == [31, 30]


def test_rows_gain_extra_fields_and_the_input_is_not_modified():
    before = copy.deepcopy(ROWS)
    out = due_reviews(ROWS, count=10)
    assert ROWS == before
    assert "interval_days" in out[0] and "overdue_days" in out[0]
    assert "interval_days" not in ROWS[0]
