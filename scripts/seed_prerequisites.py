from app.algorithms.graph import topological_sort
from app.db import get_connection

# topic: [topics you should be comfortable with first]
PREREQUISITES = {
    "Strings": ["Arrays"],
    "Hashing": ["Arrays"],
    "Two Pointers": ["Arrays"],
    "Sorting": ["Arrays"],
    "Sliding Window": ["Two Pointers"],
    "Binary Search": ["Sorting"],
    "Stacks & Queues": ["Arrays"],
    "Linked Lists": ["Arrays"],
    "Recursion": ["Stacks & Queues"],
    "Trees": ["Recursion", "Linked Lists"],
    "Graphs": ["Trees", "Stacks & Queues", "Hashing"],
    "Backtracking": ["Recursion"],
    "Heaps": ["Trees", "Sorting"],
    "Greedy": ["Sorting"],
    "Dynamic Programming": ["Recursion", "Arrays"],
}


def seed_prerequisites():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT topic_id, name FROM topics")
            ids = {row["name"]: row["topic_id"] for row in cur.fetchall()}

            edges = []
            for topic, prereqs in PREREQUISITES.items():
                for prereq in prereqs:
                    if topic not in ids or prereq not in ids:
                        raise ValueError(f"Unknown topic in edge: {prereq} -> {topic}")
                    edges.append((prereq, topic))

            order = topological_sort(list(ids), edges)  # raises on a cycle

            cur.executemany(
                "INSERT IGNORE INTO topic_prerequisites (topic_id, prereq_id) VALUES (%s, %s)",
                [(ids[topic], ids[prereq]) for prereq, topic in edges],
            )
            conn.commit()

            cur.execute("SELECT COUNT(*) AS n FROM topic_prerequisites")
            print("Prerequisite edges in database:", cur.fetchone()["n"])
            print("Learning order:", " -> ".join(order))
    finally:
        conn.close()


if __name__ == "__main__":
    seed_prerequisites()
