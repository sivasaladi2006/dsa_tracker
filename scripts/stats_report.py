from app.services.stats import (
    activity_summary,
    revision_queue,
    topic_stats,
    untouched_problems,
    weekly_activity,
)


def fmt(value, suffix=""):
    return "-" if value is None else f"{value}{suffix}"


def print_report():
    summary = activity_summary()
    print("=== ACTIVITY ===")
    print(f"{summary['active_days']} active days between {summary['first_day']} "
          f"and {summary['last_day']} ({summary['span_days']}-day span)\n")

    print("=== TOPIC STATS (weakest solve rate first) ===")
    header = f"{'Topic':<20}{'Tried':>6}{'Solved':>7}{'Solve%':>8}{'Cover%':>8}{'Att':>6}{'Min':>5}{'Days':>6}"
    print(header)
    print("-" * len(header))
    stats = sorted(topic_stats(), key=lambda r: (r["solve_pct"] is None, r["solve_pct"] or 0))
    for r in stats:
        print(f"{r['topic']:<20}{r['attempted']:>6}{r['solved']:>7}"
              f"{fmt(r['solve_pct']):>8}{fmt(r['coverage_pct']):>8}"
              f"{fmt(r['avg_attempts']):>6}{fmt(r['avg_min_solved']):>5}"
              f"{fmt(r['days_since_last']):>6}")

    queue = revision_queue()
    print(f"\n=== REVISION QUEUE ({len(queue)} problems, oldest first, top 8) ===")
    for r in queue[:8]:
        print(f"{r['title']:<40}{r['difficulty']:<8}{r['status']:<16}{r['days_ago']:>4} days ago")

    untouched = untouched_problems()
    print(f"\n=== UNTOUCHED PROBLEMS ({len(untouched)}) ===")
    for r in untouched:
        print(f"{r['title']:<48}{r['difficulty']:<8}{r['topics']}")

    print("\n=== WEEKLY ACTIVITY ===")
    weeks = weekly_activity()
    for w in weeks:
        print(f"{w['week_start']}  {'#' * w['submissions']:<10} "
              f"{w['submissions']} submissions, {w['solved']} solved")
    print(f"Total: {sum(w['submissions'] for w in weeks)} submissions")


if __name__ == "__main__":
    print_report()
