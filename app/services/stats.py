from datetime import timedelta
from decimal import Decimal

from app.db import get_connection

TOPIC_STATS_SQL = """
SELECT t.topic_id,
       t.name AS topic,
       COUNT(DISTINCT pt.problem_id) AS total_problems,
       COUNT(DISTINCT s.problem_id) AS attempted,
       COUNT(DISTINCT CASE WHEN s.status = 'Solved' THEN s.problem_id END) AS solved,
       ROUND(100 * COUNT(DISTINCT CASE WHEN s.status = 'Solved' THEN s.problem_id END)
             / NULLIF(COUNT(DISTINCT s.problem_id), 0)) AS solve_pct,
       ROUND(100 * COUNT(DISTINCT s.problem_id)
             / NULLIF(COUNT(DISTINCT pt.problem_id), 0)) AS coverage_pct,
       ROUND(AVG(s.attempts), 1) AS avg_attempts,
       ROUND(AVG(CASE WHEN s.status = 'Solved' THEN s.time_taken_min END)) AS avg_min_solved,
       DATEDIFF(CURDATE(), MAX(s.submitted_at)) AS days_since_last
FROM topics t
LEFT JOIN problem_topics pt ON pt.topic_id = t.topic_id
LEFT JOIN submissions s ON s.problem_id = pt.problem_id
GROUP BY t.topic_id, t.name
ORDER BY t.name
"""

REVISION_QUEUE_SQL = """
SELECT p.problem_id, p.title, p.difficulty, s.status, s.attempts,
       s.submitted_at, DATEDIFF(CURDATE(), s.submitted_at) AS days_ago
FROM submissions s
JOIN (SELECT problem_id, MAX(submitted_at) AS last_at
      FROM submissions GROUP BY problem_id) latest
  ON latest.problem_id = s.problem_id AND latest.last_at = s.submitted_at
JOIN problems p ON p.problem_id = s.problem_id
WHERE s.status <> 'Solved'
ORDER BY days_ago DESC
"""

UNTOUCHED_SQL = """
SELECT p.problem_id, p.title, p.difficulty,
       GROUP_CONCAT(t.name ORDER BY t.name SEPARATOR '|') AS topics
FROM problems p
JOIN problem_topics pt ON pt.problem_id = p.problem_id
JOIN topics t ON t.topic_id = pt.topic_id
LEFT JOIN submissions s ON s.problem_id = p.problem_id
WHERE s.problem_id IS NULL
GROUP BY p.problem_id, p.title, p.difficulty
ORDER BY p.problem_id
"""

WEEKLY_SQL = """
SELECT DATE_SUB(DATE(submitted_at), INTERVAL WEEKDAY(submitted_at) DAY) AS week_start,
       COUNT(*) AS submissions,
       SUM(status = 'Solved') AS solved,
       ROUND(AVG(time_taken_min)) AS avg_min
FROM submissions
GROUP BY week_start
ORDER BY week_start
"""

SUMMARY_SQL = """
SELECT COUNT(DISTINCT DATE(submitted_at)) AS active_days,
       MIN(DATE(submitted_at)) AS first_day,
       MAX(DATE(submitted_at)) AS last_day,
       DATEDIFF(MAX(submitted_at), MIN(submitted_at)) + 1 AS span_days
FROM submissions
"""


def _clean(row):
    out = {}
    for key, value in row.items():
        if isinstance(value, Decimal):
            value = int(value) if value == value.to_integral_value() else float(value)
        out[key] = value
    return out


def _fetch(sql):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            return [_clean(r) for r in cur.fetchall()]
    finally:
        conn.close()


def topic_stats():
    """One row per topic: attempted, solved, solve_pct, coverage_pct, avg_attempts,
    avg_min_solved, days_since_last (None if the topic was never practiced)."""
    return _fetch(TOPIC_STATS_SQL)


def revision_queue():
    """Problems whose latest submission is not Solved, oldest first."""
    return _fetch(REVISION_QUEUE_SQL)


def untouched_problems():
    """Problems with no submissions at all."""
    return _fetch(UNTOUCHED_SQL)


def weekly_activity():
    """Submissions per week (Monday start), with idle weeks filled in as zeros."""
    rows = _fetch(WEEKLY_SQL)
    if not rows:
        return []
    by_week = {r["week_start"]: r for r in rows}
    week, last = rows[0]["week_start"], rows[-1]["week_start"]
    filled = []
    while week <= last:
        filled.append(by_week.get(
            week, {"week_start": week, "submissions": 0, "solved": 0, "avg_min": None}
        ))
        week += timedelta(days=7)
    return filled


def activity_summary():
    rows = _fetch(SUMMARY_SQL)
    return rows[0] if rows else {}
