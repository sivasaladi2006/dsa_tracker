from datetime import datetime

import pymysql

from app.db import get_connection

SELECT_ROW = (
    "SELECT s.submission_id, s.problem_id, p.title, s.status, s.attempts, "
    "s.time_taken_min, s.submitted_at, s.notes "
    "FROM submissions s JOIN problems p ON p.problem_id = s.problem_id "
)


class ProblemNotFound(Exception):
    pass


def create_submission(data):
    """Insert a submission (a SubmissionCreate) and return the saved row."""
    when = (data.submitted_at or datetime.now()).replace(microsecond=0)
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM problems WHERE problem_id = %s", (data.problem_id,))
            if cur.fetchone() is None:
                raise ProblemNotFound(data.problem_id)
            try:
                cur.execute(
                    "INSERT INTO submissions "
                    "(problem_id, status, attempts, time_taken_min, submitted_at, notes) "
                    "VALUES (%s, %s, %s, %s, %s, %s)",
                    (data.problem_id, data.status, data.attempts,
                     data.time_taken_min, when, data.notes),
                )
            except pymysql.err.IntegrityError as exc:
                raise ProblemNotFound(data.problem_id) from exc
            new_id = cur.lastrowid
            cur.execute(SELECT_ROW + "WHERE s.submission_id = %s", (new_id,))
            row = cur.fetchone()
        conn.commit()
        return row
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def recent_submissions(limit=10):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                SELECT_ROW + "ORDER BY s.submitted_at DESC, s.submission_id DESC LIMIT %s",
                (limit,),
            )
            return cur.fetchall()
    finally:
        conn.close()
