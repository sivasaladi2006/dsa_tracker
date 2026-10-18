from app.algorithms.sorting import merge_sort

ATTEMPTED_INTERVAL = 2
NEEDS_REVISION_INTERVAL = 3
SOLVED_INTERVALS = [          # (minimum attempts, days until review), checked top down
    (3, 7),
    (2, 14),
    (1, 30),
]


def review_interval(status, attempts):
    """Days to wait after the latest submission before reviewing a problem again."""
    if status == "Attempted":
        return ATTEMPTED_INTERVAL
    if status == "Needs Revision":
        return NEEDS_REVISION_INTERVAL
    for min_attempts, days in SOLVED_INTERVALS:
        if attempts >= min_attempts:
            return days
    return SOLVED_INTERVALS[-1][1]


def due_reviews(latest_rows, count=5):
    """Problems due for review, most urgent first.

    latest_rows: rows from latest_submissions(). Unsolved problems come before
    solved ones; within each group, the most overdue comes first.
    """
    due = []
    for row in latest_rows:
        interval = review_interval(row["status"], row["attempts"])
        overdue = row["days_ago"] - interval
        if overdue >= 0:
            due.append({**row, "interval_days": interval, "overdue_days": overdue})
    ranked = merge_sort(
        due,
        key=lambda r: (r["status"] == "Solved", -r["overdue_days"], r["problem_id"]),
    )
    return ranked[:count]
