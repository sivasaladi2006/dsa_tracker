from app.algorithms.graph import prerequisite_map, unmet_prerequisites
from app.algorithms.sorting import merge_sort
from app.db import get_connection
from app.services.scoring import weakness_score
from app.services.stats import topic_stats

MASTERED_BELOW = 0.35           # weakness score under this counts as mastered...
MIN_ATTEMPTED_FOR_MASTERY = 3   # ...but only with at least this many problems tried


def rank_focus_topics(stats_rows, prereqs, limit=3):
    """Pick which topics to practice next, redirecting to unmet prerequisites.

    stats_rows: rows shaped like topic_stats() output.
    prereqs: {topic: [prerequisite topics]}.
    Returns up to `limit` dicts: topic, score, components, requested_by, path.
    """
    scores = {r["topic"]: weakness_score(r) for r in stats_rows}
    mastered = {
        r["topic"]
        for r in stats_rows
        if (r["attempted"] or 0) >= MIN_ATTEMPTED_FOR_MASTERY
        and scores[r["topic"]]["score"] < MASTERED_BELOW
    }

    def score_of(name):
        return scores[name]["score"] if name in scores else 0.0

    def resolve(topic):
        """Follow nearest unmet prerequisites down to one with no unmet prerequisites."""
        path = [topic]
        while True:
            gaps = unmet_prerequisites(topic, prereqs, mastered)
            if not gaps:
                return topic, path
            nearest = min(dist for _, dist in gaps)
            topic = max((n for n, dist in gaps if dist == nearest), key=score_of)
            path.append(topic)

    ranked = merge_sort(stats_rows, key=lambda r: scores[r["topic"]]["score"], reverse=True)
    focus, seen = [], set()
    for row in ranked:
        original = row["topic"]
        if original in mastered:
            continue
        target, path = resolve(original)
        if target in seen:
            continue
        seen.add(target)
        focus.append({
            "topic": target,
            "score": score_of(target),
            "components": scores[target]["components"] if target in scores else {},
            "requested_by": original if target != original else None,
            "path": path,
        })
        if len(focus) == limit:
            break
    return focus


def load_prereqs():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT p.name AS prereq, t.name AS topic FROM topic_prerequisites tp "
                "JOIN topics t ON t.topic_id = tp.topic_id "
                "JOIN topics p ON p.topic_id = tp.prereq_id"
            )
            return prerequisite_map([(r["prereq"], r["topic"]) for r in cur.fetchall()])
    finally:
        conn.close()


def focus_topics(limit=3):
    return rank_focus_topics(topic_stats(), load_prereqs(), limit)
