from app.db import get_connection

TOPICS = [
    "Arrays", "Strings", "Hashing", "Two Pointers", "Sliding Window",
    "Binary Search", "Sorting", "Stacks & Queues", "Linked Lists",
    "Recursion", "Trees", "Graphs", "Backtracking", "Heaps", "Greedy",
    "Dynamic Programming",
]


def seed_topics():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.executemany(
                "INSERT IGNORE INTO topics (name) VALUES (%s)",
                [(name,) for name in TOPICS],
            )
            conn.commit()
            cur.execute("SELECT COUNT(*) AS n FROM topics")
            print("Topics in database:", cur.fetchone()["n"])
    finally:
        conn.close()


if __name__ == "__main__":
    seed_topics()
