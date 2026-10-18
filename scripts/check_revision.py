from app.services.revision import due_reviews, review_interval


def row(pid, status, attempts, days_ago):
    return {"problem_id": pid, "title": f"P{pid}", "difficulty": "Medium",
            "status": status, "attempts": attempts, "days_ago": days_ago, "topics": "T"}


def ids(rows):
    return [r["problem_id"] for r in rows]


# Interval table
assert review_interval("Attempted", 5) == 2
assert review_interval("Needs Revision", 1) == 3
assert review_interval("Solved", 1) == 30
assert review_interval("Solved", 2) == 14
assert review_interval("Solved", 3) == 7
assert review_interval("Solved", 6) == 7

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

out = due_reviews(ROWS, count=10)
assert ids(out) == [1, 2, 6, 8, 4, 7], ids(out)                        # unsolved first, then by overdue; 4 before 7 on the tie
assert [r["overdue_days"] for r in out] == [3, 0, 6, 3, 0, 0]
assert ids(due_reviews(ROWS, count=3)) == [1, 2, 6]                    # count limit
assert due_reviews([], count=5) == []                                  # nothing attempted
assert due_reviews([row(9, "Solved", 1, 5)]) == []                     # nothing due
assert "interval_days" not in ROWS[0]                                  # input rows are not modified
assert ids(ROWS) == [1, 2, 3, 4, 5, 6, 7, 8]

print("Revision checks passed")
