from app.algorithms.sorting import merge_sort
from app.services.scoring import smoothed_solve_rate

DIFFICULTY_LEVEL = {"Easy": 0, "Medium": 1, "Hard": 2}
EASY_BELOW = 0.50          # smoothed solve rate under this: practice Easy problems
HARD_AT_OR_ABOVE = 0.75    # at or above this: practice Hard problems


def target_difficulty(stats):
    """Difficulty to aim at, from the topic's smoothed solve rate."""
    rate = smoothed_solve_rate(stats.get("solved") or 0, stats.get("attempted") or 0)
    if rate < EASY_BELOW:
        return "Easy"
    if rate >= HARD_AT_OR_ABOVE:
        return "Hard"
    return "Medium"


def pick_problems(candidates, target, count=3, bonus_topics=frozenset()):
    """Best `count` candidates: nearest to the target difficulty, then bonus-topic
    overlap, then original problem order.

    candidates: dicts with problem_id, title, difficulty and topics ('A|B' string).
    """
    goal = DIFFICULTY_LEVEL[target]

    def key(problem):
        distance = abs(DIFFICULTY_LEVEL[problem["difficulty"]] - goal)
        overlap = len(set(problem["topics"].split("|")) & set(bonus_topics))
        return (distance, -overlap, problem["problem_id"])

    return merge_sort(candidates, key=key)[:count]


def suggest_new_problems(focus, stats_rows, untouched_rows, count=3):
    """New problems for one focus entry from rank_focus_topics().

    stats_rows: topic_stats() rows. untouched_rows: untouched_problems() rows.
    """
    topic = focus["topic"]
    stats = next((r for r in stats_rows if r["topic"] == topic), {})
    candidates = [p for p in untouched_rows if topic in p["topics"].split("|")]
    target = target_difficulty(stats)
    bonus = {focus["requested_by"]} if focus.get("requested_by") else set()
    return {
        "topic": topic,
        "target_difficulty": target,
        "problems": pick_problems(candidates, target, count, bonus),
    }
