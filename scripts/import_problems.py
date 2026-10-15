import csv
from pathlib import Path

from app.db import get_connection

CSV_PATH = Path(__file__).resolve().parent.parent / "data" / "problems.csv"
PLATFORM = "LeetCode"
VALID_DIFFICULTIES = {"Easy", "Medium", "Hard"}


def import_problems():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT topic_id, name FROM topics")
            topic_ids = {r["name"]: r["topic_id"] for r in cur.fetchall()}

            with open(CSV_PATH, newline="") as f:
                for row in csv.DictReader(f):
                    title = row["title"].strip()
                    difficulty = row["difficulty"].strip()
                    topics = [t.strip() for t in row["topics"].split("|")]

                    if difficulty not in VALID_DIFFICULTIES:
                        raise ValueError(f"Bad difficulty for '{title}': {difficulty}")
                    unknown = [t for t in topics if t not in topic_ids]
                    if unknown:
                        raise ValueError(f"Unknown topic(s) for '{title}': {unknown}")

                    cur.execute(
                        "INSERT IGNORE INTO problems (title, platform, difficulty) "
                        "VALUES (%s, %s, %s)",
                        (title, PLATFORM, difficulty),
                    )
                    cur.execute(
                        "SELECT problem_id FROM problems WHERE platform = %s AND title = %s",
                        (PLATFORM, title),
                    )
                    problem_id = cur.fetchone()["problem_id"]
                    cur.executemany(
                        "INSERT IGNORE INTO problem_topics (problem_id, topic_id) "
                        "VALUES (%s, %s)",
                        [(problem_id, topic_ids[t]) for t in topics],
                    )
        conn.commit()

        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS n FROM problems")
            print("Problems in database:", cur.fetchone()["n"])
            cur.execute("SELECT COUNT(*) AS n FROM problem_topics")
            print("Problem-topic links in database:", cur.fetchone()["n"])
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    import_problems()
