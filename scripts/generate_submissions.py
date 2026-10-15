import csv
import random
from collections import Counter
from datetime import date, datetime, time, timedelta
from pathlib import Path
from statistics import mean

from app.db import get_connection

SEED = 42
WINDOW_DAYS = 90
OUT_PATH = Path(__file__).resolve().parent.parent / "data" / "submissions_sample.csv"

# topic: (skill 0-1, share of its problems attempted, days since last practice)
PROFILES = {
    "Arrays": (0.85, 0.95, 1),
    "Strings": (0.80, 0.90, 1),
    "Hashing": (0.80, 0.90, 2),
    "Sorting": (0.75, 0.80, 5),
    "Two Pointers": (0.70, 0.80, 4),
    "Linked Lists": (0.70, 0.80, 10),
    "Stacks & Queues": (0.65, 0.70, 7),
    "Binary Search": (0.60, 0.70, 8),
    "Heaps": (0.60, 0.60, 45),
    "Sliding Window": (0.55, 0.70, 6),
    "Recursion": (0.55, 0.70, 6),
    "Trees": (0.50, 0.70, 3),
    "Greedy": (0.50, 0.50, 12),
    "Backtracking": (0.35, 0.60, 5),
    "Graphs": (0.30, 0.60, 4),
    "Dynamic Programming": (0.30, 0.70, 2),
}
DIFFICULTY_ADJUST = {"Easy": 0.15, "Medium": 0.0, "Hard": -0.25}
BASE_MINUTES = {"Easy": 15, "Medium": 30, "Hard": 55}


def load_problems():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT p.title, p.difficulty, "
                "GROUP_CONCAT(t.name SEPARATOR '|') AS topics "
                "FROM problems p "
                "JOIN problem_topics pt ON pt.problem_id = p.problem_id "
                "JOIN topics t ON t.topic_id = pt.topic_id "
                "GROUP BY p.problem_id, p.title, p.difficulty "
                "ORDER BY p.problem_id"
            )
            return cur.fetchall()
    finally:
        conn.close()


def run_session(rng, skill, difficulty):
    p_clean = min(max(skill, 0.05), 0.95)
    roll = rng.random()
    if roll < p_clean:
        status = "Solved"
        attempts = 1 if rng.random() < 0.7 else 2
    elif roll < p_clean + (1 - p_clean) * 0.5:
        status = "Needs Revision"
        attempts = rng.randint(2, 4)
    else:
        status = "Attempted"
        attempts = rng.randint(2, 5)
    minutes = BASE_MINUTES[difficulty] * rng.uniform(0.7, 1.3)
    minutes *= (1 + 0.3 * (attempts - 1)) * (1.3 - 0.6 * p_clean)
    return status, attempts, min(int(round(minutes)), 180)


def make_timestamp(rng, days_ago):
    day = date.today() - timedelta(days=days_ago)
    return datetime.combine(day, time(rng.randint(8, 23), rng.randint(0, 59)))


def generate_rows():
    rng = random.Random(SEED)
    rows = []
    for prob in load_problems():
        topics = prob["topics"].split("|")
        skill = mean(PROFILES[t][0] for t in topics) + DIFFICULTY_ADJUST[prob["difficulty"]]
        coverage = mean(PROFILES[t][1] for t in topics)
        latest_ago = max(1, round(mean(PROFILES[t][2] for t in topics)))

        if rng.random() > coverage:
            continue  # this problem was never attempted

        days_ago = rng.randint(latest_ago, WINDOW_DAYS)
        sessions = 0
        while True:
            status, attempts, minutes = run_session(rng, skill, prob["difficulty"])
            ts = make_timestamp(rng, days_ago)
            rows.append((prob["title"], status, attempts, minutes,
                         ts.strftime("%Y-%m-%d %H:%M:%S"), ""))
            sessions += 1
            if status == "Solved" or sessions == 3 or rng.random() > 0.6:
                break
            days_ago = max(latest_ago, days_ago - rng.randint(1, 10))
            skill += 0.15  # retrying helps a little

    rows.sort(key=lambda r: r[4])
    return rows


if __name__ == "__main__":
    rows = generate_rows()
    with open(OUT_PATH, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["title", "status", "attempts", "time_taken_min", "submitted_at", "notes"])
        writer.writerows(rows)
    print("Submissions written:", len(rows))
    print("Distinct problems attempted:", len({r[0] for r in rows}))
    print("By status:", dict(Counter(r[1] for r in rows)))
