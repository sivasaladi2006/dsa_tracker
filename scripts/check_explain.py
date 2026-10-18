from app.services.explain import explain_focus, explain_new_problem, explain_review

# Top two contributors: low_solve (0.27) and staleness (0.2); struggle (0.16) is third
GRAPHS = {"topic": "Graphs", "score": 0.66, "requested_by": None, "path": ["Graphs"],
          "components": {"low_solve": 0.27, "struggle": 0.16, "staleness": 0.2, "coverage_gap": 0.03}}
GRAPHS_STATS = {"attempted": 4, "solved": 1, "avg_attempts": 2.6, "days_since_last": 35,
                "coverage_pct": 80, "total_problems": 5}
assert explain_focus(GRAPHS, GRAPHS_STATS) == (
    "Graphs (score 0.66): you solved 1 of 4 problems tried (25%) and you haven't "
    "practiced it in 35 days. Only 4 problems tried so far, so treat this as a rough signal."
)

# Redirected topic: low_solve (0.206) and struggle (0.13) are the top two
STACKS = {"topic": "Stacks & Queues", "score": 0.447, "requested_by": "Graphs",
          "path": ["Graphs", "Stacks & Queues"],
          "components": {"low_solve": 0.206, "struggle": 0.13, "staleness": 0.04, "coverage_gap": 0.064}}
STACKS_STATS = {"attempted": 4, "solved": 2, "avg_attempts": 2.3, "days_since_last": 6,
                "coverage_pct": 57, "total_problems": 7}
text = explain_focus(STACKS, STACKS_STATS)
assert text.startswith("Graphs ranks higher, but it depends on Stacks & Queues "
                       "(path: Graphs -> Stacks & Queues), so start here. "), text
assert "you solved 2 of 4 problems tried (50%)" in text
assert "it takes about 2.3 attempts per problem" in text
assert "staleness" not in text and "6 days" not in text      # third place is not mentioned

# Never practiced: a single plain sentence, no small-sample warning
NEVER = {"topic": "Heaps", "score": 0.63, "requested_by": None, "path": ["Heaps"],
         "components": {"low_solve": 0.18, "struggle": 0.1, "staleness": 0.2, "coverage_gap": 0.15}}
assert explain_focus(NEVER, {"attempted": 0, "solved": 0}) == "Heaps (score 0.63): you haven't started it yet."

# Plenty of data: no warning
BIG = {"topic": "DP", "score": 0.5, "requested_by": None, "path": ["DP"],
       "components": {"low_solve": 0.27, "struggle": 0.1, "staleness": 0.147, "coverage_gap": 0.0}}
BIG_STATS = {"attempted": 10, "solved": 4, "avg_attempts": 2.0, "days_since_last": 22,
             "coverage_pct": 100, "total_problems": 10}
text = explain_focus(BIG, BIG_STATS)
assert text == ("DP (score 0.5): you solved 4 of 10 problems tried (40%) and you haven't "
                "practiced it in 22 days."), text

# Coverage gap alone: weaker signals under 0.03 are dropped
COVER = {"topic": "Z", "score": 0.2, "requested_by": None, "path": ["Z"],
         "components": {"low_solve": 0.01, "struggle": 0.0, "staleness": 0.02, "coverage_gap": 0.12}}
COVER_STATS = {"attempted": 6, "solved": 6, "avg_attempts": 1.0, "days_since_last": 3,
               "coverage_pct": 60, "total_problems": 10}
assert explain_focus(COVER, COVER_STATS) == "Z (score 0.2): 4 of its 10 problems are untouched."

# Nothing contributes enough: fallback sentence
assert explain_focus({"topic": "T", "score": 0.1, "requested_by": None, "path": ["T"], "components": {}},
                     {"attempted": 6, "solved": 6, "avg_attempts": 1.0, "days_since_last": 1,
                      "coverage_pct": 100, "total_problems": 6}) \
    == "T (score 0.1): it is the next best option by score."

# New problems
FOCUS = {"topic": "Stacks & Queues", "requested_by": "Graphs"}
assert explain_new_problem(
    {"title": "Rotting Oranges", "difficulty": "Medium", "topics": "Graphs|Stacks & Queues"},
    "Medium", FOCUS,
) == ("Rotting Oranges: new Medium problem in Stacks & Queues; matches your target level "
      "(Medium). It also covers Graphs, so it advances both.")
assert explain_new_problem(
    {"title": "Implement Queue using Stacks", "difficulty": "Easy", "topics": "Stacks & Queues"},
    "Medium", FOCUS,
) == ("Implement Queue using Stacks: new Easy problem in Stacks & Queues; closest untouched "
      "match to your target level (Medium).")

# Reviews, including singular and plural attempts
assert explain_review({"title": "Maximum Subarray", "status": "Needs Revision", "attempts": 3,
                       "days_ago": 10, "interval_days": 3, "overdue_days": 7}) == (
    "Maximum Subarray: last result was Needs Revision after 3 attempts, 10 days ago; "
    "due after 3 days, so 7 days overdue.")
assert explain_review({"title": "Two Sum", "status": "Solved", "attempts": 1,
                       "days_ago": 40, "interval_days": 30, "overdue_days": 10}) == (
    "Two Sum: last result was Solved after 1 attempt, 40 days ago; "
    "due after 30 days, so 10 days overdue.")

print("Explanation checks passed")
