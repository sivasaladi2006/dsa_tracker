import csv
import sys
from pathlib import Path

from app.db import get_connection

CSV_PATH = Path(__file__).resolve().parent.parent / "data" / "submissions_sample.csv"
PLATFORM = "LeetCode"


def import_submissions(replace=False):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS n FROM submissions")
            existing = cur.fetchone()["n"]
            if existing and not replace:
                print(f"submissions already has {existing} rows. "
                      "Re-run with --replace to wipe and reload.")
                return
            if replace:
                cur.execute("DELETE FROM submissions")

            cur.execute(
                "SELECT problem_id, title FROM problems WHERE platform = %s", (PLATFORM,)
            )
            ids = {r["title"]: r["problem_id"] for r in cur.fetchall()}

            rows = []
            with open(CSV_PATH, newline="") as f:
                for r in csv.DictReader(f):
                    if r["title"] not in ids:
                        raise ValueError(f"Unknown problem title: {r['title']}")
                    rows.append((
                        ids[r["title"]], r["status"], int(r["attempts"]),
                        int(r["time_taken_min"]), r["submitted_at"], r["notes"] or None,
                    ))

            cur.executemany(
                "INSERT INTO submissions "
                "(problem_id, status, attempts, time_taken_min, submitted_at, notes) "
                "VALUES (%s, %s, %s, %s, %s, %s)",
                rows,
            )
        conn.commit()

        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS n FROM submissions")
            print("Submissions in database:", cur.fetchone()["n"])
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    import_submissions(replace="--replace" in sys.argv)
