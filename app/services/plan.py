from app.services.explain import explain_focus, explain_new_problem, explain_review
from app.services.problem_picker import suggest_new_problems
from app.services.recommender import load_prereqs, rank_focus_topics
from app.services.revision import due_reviews
from app.services.stats import latest_submissions, topic_stats, untouched_problems


def review_entries(latest_rows, count):
    """Due reviews in API shape: title, difficulty, status, overdue_days, why."""
    return [
        {
            "title": r["title"],
            "difficulty": r["difficulty"],
            "status": r["status"],
            "overdue_days": r["overdue_days"],
            "why": explain_review(r),
        }
        for r in due_reviews(latest_rows, count)
    ]


def build_plan(stats_rows, prereqs, untouched_rows, latest_rows,
               focus_count=3, problems_per_topic=3, review_count=3):
    """Pure function: turn the data into a practice plan (a dict, ready for JSON)."""
    stats_by_topic = {r["topic"]: r for r in stats_rows}

    focus_entries = []
    for focus in rank_focus_topics(stats_rows, prereqs, focus_count):
        picks = suggest_new_problems(focus, stats_rows, untouched_rows, problems_per_topic)
        focus_entries.append({
            "topic": focus["topic"],
            "score": focus["score"],
            "requested_by": focus["requested_by"],
            "why": explain_focus(focus, stats_by_topic.get(focus["topic"], {})),
            "target_difficulty": picks["target_difficulty"],
            "new_problems": [
                {
                    "title": p["title"],
                    "difficulty": p["difficulty"],
                    "why": explain_new_problem(p, picks["target_difficulty"], focus),
                }
                for p in picks["problems"]
            ],
        })

    return {"focus": focus_entries, "reviews": review_entries(latest_rows, review_count)}


def recommend(focus_count=3, problems_per_topic=3, review_count=3):
    """Load the real data and build the plan."""
    return build_plan(
        topic_stats(), load_prereqs(), untouched_problems(), latest_submissions(),
        focus_count, problems_per_topic, review_count,
    )


def render_plan(plan):
    lines = ["FOCUS TOPICS"]
    if not plan["focus"]:
        lines.append("Nothing to focus on: every topic looks solid.")
    for i, entry in enumerate(plan["focus"], start=1):
        lines.append(f"{i}. {entry['why']}")
        if entry["new_problems"]:
            lines.append("   New problems:")
            for p in entry["new_problems"]:
                lines.append(f"   - {p['why']}")
        else:
            lines.append("   No untouched problems left in this topic; see reviews.")
    lines.append("")
    lines.append("REVIEWS DUE")
    if not plan["reviews"]:
        lines.append("Nothing due for review.")
    for r in plan["reviews"]:
        lines.append(f"- {r['why']}")
    return "\n".join(lines)
