from datetime import date

from app.services.plan import build_plan, render_plan
from app.services.recommender import load_prereqs
from app.services.stats import activity_summary, latest_submissions, topic_stats, untouched_problems

STRONG_TOPICS = {"Trees", "Recursion"}   # built into the sample data as strengths


def load_as_of_last_submission():
    """Load the data with every 'days since' field rewound to the last submission day."""
    last_day = activity_summary()["last_day"]
    offset = (date.today() - last_day).days
    stats = []
    for row in topic_stats():
        row = dict(row)
        if row["days_since_last"] is not None:
            row["days_since_last"] = max(0, row["days_since_last"] - offset)
        stats.append(row)
    latest = []
    for row in latest_submissions():
        row = dict(row)
        row["days_ago"] = max(0, row["days_ago"] - offset)
        latest.append(row)
    return stats, latest, last_day, offset


def main():
    stats, latest, last_day, offset = load_as_of_last_submission()
    prereqs = load_prereqs()
    untouched = untouched_problems()
    topics_of = {p["title"]: p["topics"].split("|") for p in untouched}
    attempted_titles = {r["title"] for r in latest}

    plan = build_plan(stats, prereqs, untouched, latest,
                      focus_count=5, problems_per_topic=3, review_count=5)
    focus = plan["focus"]
    focus_names = [f["topic"] for f in focus]
    requested = {f["requested_by"] for f in focus if f["requested_by"]}

    # 1-3. The known weak spots are found, and the known strengths are left alone
    assert "Graphs" in focus_names or "Graphs" in requested, ("Graphs missing", focus_names)
    assert "Dynamic Programming" in focus_names, ("Dynamic Programming missing", focus_names)
    assert not (STRONG_TOPICS & set(focus_names)), ("strong topic recommended", focus_names)

    # 4. No topic is recommended twice
    assert len(focus_names) == len(set(focus_names)), focus_names

    # 5. Every new problem is untouched, belongs to its topic, and appears only once
    seen_titles = []
    for entry in focus:
        assert len(entry["new_problems"]) <= 3, entry
        for p in entry["new_problems"]:
            assert p["title"] not in attempted_titles, ("already attempted", p["title"])
            assert entry["topic"] in topics_of[p["title"]], ("wrong topic", p["title"], entry["topic"])
            seen_titles.append(p["title"])
    assert len(seen_titles) == len(set(seen_titles)), seen_titles

    # 6. Reviews: unsolved problems come before solved ones, most overdue first within each group
    reviews = plan["reviews"]
    assert reviews, "expected at least one review due"
    assert reviews[0]["status"] != "Solved", reviews[0]
    solved_flags = [r["status"] == "Solved" for r in reviews]
    assert solved_flags == sorted(solved_flags), solved_flags
    for flag in (False, True):
        group = [r["overdue_days"] for r in reviews if (r["status"] == "Solved") == flag]
        assert group == sorted(group, reverse=True), group

    print(f"Validation passed (data viewed as of {last_day}, rewound {offset} days from today)")
    print(f"Focus topics: {focus_names}")
    print(f"Redirected from: {sorted(requested)}\n")
    top3 = build_plan(stats, prereqs, untouched, latest,
                      focus_count=3, problems_per_topic=3, review_count=3)
    print(render_plan(top3))


if __name__ == "__main__":
    main()
