from app.services.plan import build_plan, render_plan


def stats(topic, attempted, solved, avg_attempts, days, coverage, total):
    return {"topic": topic, "attempted": attempted, "solved": solved,
            "avg_attempts": avg_attempts, "days_since_last": days,
            "coverage_pct": coverage, "total_problems": total}


STATS = [
    stats("A", 10, 10, 1.0, 1, 100, 10),   # score about 0.05: mastered
    stats("B", 8, 4, 2.0, 22, 80, 10),     # score about 0.49
    stats("C", 4, 1, 2.6, 35, 80, 5),      # score about 0.66
    stats("D", 5, 3, 1.8, 10, 50, 10),     # score about 0.40
]
PREREQS = {"C": ["B"], "B": ["A"]}
UNTOUCHED = [
    {"problem_id": 1, "title": "B-Easy", "difficulty": "Easy", "topics": "B"},
    {"problem_id": 2, "title": "B-Medium", "difficulty": "Medium", "topics": "B"},
    {"problem_id": 3, "title": "C-Medium", "difficulty": "Medium", "topics": "B|C"},
    {"problem_id": 4, "title": "D-Hard", "difficulty": "Hard", "topics": "D"},
    {"problem_id": 5, "title": "D-Medium", "difficulty": "Medium", "topics": "D"},
]


def latest(pid, title, status, attempts, days_ago):
    return {"problem_id": pid, "title": title, "difficulty": "Medium", "status": status,
            "attempts": attempts, "days_ago": days_ago, "topics": "T"}


LATEST = [
    latest(10, "R-Old", "Needs Revision", 2, 13),   # interval 3, overdue 10
    latest(11, "R-Solved", "Solved", 1, 40),        # interval 30, overdue 10
    latest(12, "R-NotDue", "Solved", 1, 5),         # not due
    latest(13, "R-Attempted", "Attempted", 4, 4),   # interval 2, overdue 2
]

plan = build_plan(STATS, PREREQS, UNTOUCHED, LATEST, focus_count=3, problems_per_topic=2, review_count=3)

# Focus: C is redirected to B; B is then skipped as a duplicate; D follows; A is mastered
assert [f["topic"] for f in plan["focus"]] == ["B", "D"], plan["focus"]
b, d = plan["focus"]
assert b["requested_by"] == "C" and d["requested_by"] is None
assert b["why"].startswith("C ranks higher, but it depends on B (path: C -> B), so start here.")
assert "you solved 4 of 8 problems tried (50%)" in b["why"]
assert "D (score 0.402): you solved 3 of 5 problems tried (60%) and it takes about 1.8 attempts per problem." in d["why"]

# New problems: C-Medium leads for B because it also covers C, the topic that asked for the redirect
assert b["target_difficulty"] == "Medium" and d["target_difficulty"] == "Medium"
assert [p["title"] for p in b["new_problems"]] == ["C-Medium", "B-Medium"]
assert [p["title"] for p in d["new_problems"]] == ["D-Medium", "D-Hard"]
assert "It also covers C, so it advances both." in b["new_problems"][0]["why"]

# Reviews: unsolved first by overdue days, solved after, and the not-due problem is excluded
assert [r["title"] for r in plan["reviews"]] == ["R-Old", "R-Attempted", "R-Solved"]
assert plan["reviews"][0]["overdue_days"] == 10

# Limits are respected
small = build_plan(STATS, PREREQS, UNTOUCHED, LATEST, focus_count=1, problems_per_topic=1, review_count=1)
assert [f["topic"] for f in small["focus"]] == ["B"]
assert [p["title"] for p in small["focus"][0]["new_problems"]] == ["C-Medium"]
assert [r["title"] for r in small["reviews"]] == ["R-Old"]

# Edge cases: no data at all, and everything mastered
assert build_plan([], {}, [], []) == {"focus": [], "reviews": []}
mastered_only = build_plan([STATS[0]], {}, [], [])
assert mastered_only["focus"] == []
assert "Nothing to focus on" in render_plan(mastered_only)
assert "Nothing due for review." in render_plan(mastered_only)

# Rendering
text = render_plan(plan)
assert text.startswith("FOCUS TOPICS\n1. C ranks higher"), text
assert "   New problems:\n   - C-Medium: new Medium problem in B;" in text
assert "\n2. D (score 0.402)" in text
assert "\n\nREVIEWS DUE\n- R-Old: last result was Needs Revision after 2 attempts, 13 days ago;" in text

# A topic with no untouched problems left says so
no_new = render_plan(build_plan(STATS, PREREQS, [], LATEST))
assert "No untouched problems left in this topic; see reviews." in no_new

print("Plan checks passed")
