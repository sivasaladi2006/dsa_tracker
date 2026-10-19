from app.db import get_connection

# Attaches each problem's most recent submission (if any) as `ls`.
LATEST_JOIN = """
LEFT JOIN submissions ls ON ls.submission_id = (
    SELECT s2.submission_id FROM submissions s2
    WHERE s2.problem_id = p.problem_id
    ORDER BY s2.submitted_at DESC, s2.submission_id DESC LIMIT 1)
"""


def _query(sql, params=()):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchall()
    finally:
        conn.close()


def list_topics():
    return _query("SELECT topic_id, name FROM topics ORDER BY name")


def find_topic(name):
    """Case-insensitive lookup. Returns the stored topic name, or None."""
    rows = _query("SELECT name FROM topics WHERE LOWER(name) = LOWER(%s)", (name,))
    return rows[0]["name"] if rows else None


def list_problems(topic=None, difficulty=None, status=None, limit=50, offset=0):
    """A page of problems plus the total that match the filters."""
    where, params = [], []
    if topic:
        where.append(
            "EXISTS (SELECT 1 FROM problem_topics pt2 "
            "JOIN topics t2 ON t2.topic_id = pt2.topic_id "
            "WHERE pt2.problem_id = p.problem_id AND t2.name = %s)"
        )
        params.append(topic)
    if difficulty:
        where.append("p.difficulty = %s")
        params.append(difficulty)
    if status == "Untouched":
        where.append("ls.submission_id IS NULL")
    elif status:
        where.append("ls.status = %s")
        params.append(status)
    where_sql = ("WHERE " + " AND ".join(where)) if where else ""

    total = _query(
        f"SELECT COUNT(*) AS n FROM problems p {LATEST_JOIN} {where_sql}", params
    )[0]["n"]

    rows = _query(
        "SELECT p.problem_id, p.title, p.difficulty, ls.status AS latest_status, "
        "(SELECT GROUP_CONCAT(t.name ORDER BY t.name SEPARATOR '|') "
        " FROM problem_topics pt JOIN topics t ON t.topic_id = pt.topic_id "
        " WHERE pt.problem_id = p.problem_id) AS topics "
        f"FROM problems p {LATEST_JOIN} {where_sql} "
        "ORDER BY p.problem_id LIMIT %s OFFSET %s",
        params + [limit, offset],
    )
    for row in rows:
        row["topics"] = [t for t in (row["topics"] or "").split("|") if t]
    return {"total": total, "limit": limit, "offset": offset, "items": rows}
