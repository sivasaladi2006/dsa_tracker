import pytest

from app.services.explain import explain_focus, explain_new_problem, explain_review

# Top two contributors: low_solve (0.27) and staleness (0.2); struggle (0.16) is third.
GRAPHS = {"topic": "Graphs", "score": 0.66, "requested_by": None, "path": ["Graphs"],
          "components": {"low_solve": 0.27, "struggle": 0.16, "staleness": 0.2, "coverage_gap": 0.03}}
GRAPHS_STATS = {"attempted": 4, "solved": 1, "avg_attempts": 2.6, "days_since_last": 35,
                "coverage_pct": 80, "total_problems": 5}


def test_focus_names_the_two_biggest_reasons_and_warns_about_a_small_sample():
    assert explain_focus(GRAPHS, GRAPHS_STATS) == (
        "Graphs (score 0.66): you solved 1 of 4 problems tried (25%) and you haven't "
        "practiced it in 35 days. Only 4 problems tried so far, so treat this as a rough signal."
    )


def test_redirected_focus_explains_the_redirect():
    focus = {"topic": "Stacks & Queues", "score": 0.447, "requested_by": "Graphs",
             "path": ["Graphs", "Stacks & Queues"],
             "components": {"low_solve": 0.206, "struggle": 0.13, "staleness": 0.04, "coverage_gap": 0.064}}
    stats = {"attempted": 4, "solved": 2, "avg_attempts": 2.3, "days_since_last": 6,
             "coverage_pct": 57, "total_problems": 7}
    text = explain_focus(focus, stats)
    assert text.startswith(
        "Graphs ranks higher, but it depends on Stacks & Queues "
        "(path: Graphs -> Stacks & Queues), so start here. "
    )
    assert "you solved 2 of 4 problems tried (50%)" in text
    assert "it takes about 2.3 attempts per problem" in text
    assert "6 days" not in text          # staleness is third place, so it is not mentioned


def test_never_practiced_topic_gets_one_plain_sentence():
    focus = {"topic": "Heaps", "score": 0.63, "requested_by": None, "path": ["Heaps"],
             "components": {"low_solve": 0.18, "struggle": 0.1, "staleness": 0.2, "coverage_gap": 0.15}}
    assert explain_focus(focus, {"attempted": 0, "solved": 0}) == "Heaps (score 0.63): you haven't started it yet."


def test_plenty_of_data_has_no_warning():
    focus = {"topic": "DP", "score": 0.5, "requested_by": None, "path": ["DP"],
             "components": {"low_solve": 0.27, "struggle": 0.1, "staleness": 0.147, "coverage_gap": 0.0}}
    stats = {"attempted": 10, "solved": 4, "avg_attempts": 2.0, "days_since_last": 22,
             "coverage_pct": 100, "total_problems": 10}
    assert explain_focus(focus, stats) == (
        "DP (score 0.5): you solved 4 of 10 problems tried (40%) and you haven't practiced it in 22 days."
    )


def test_weak_signals_are_dropped():
    focus = {"topic": "Z", "score": 0.2, "requested_by": None, "path": ["Z"],
             "components": {"low_solve": 0.01, "struggle": 0.0, "staleness": 0.02, "coverage_gap": 0.12}}
    stats = {"attempted": 6, "solved": 6, "avg_attempts": 1.0, "days_since_last": 3,
             "coverage_pct": 60, "total_problems": 10}
    assert explain_focus(focus, stats) == "Z (score 0.2): 4 of its 10 problems are untouched."


def test_fallback_when_no_signal_contributes_enough():
    focus = {"topic": "T", "score": 0.1, "requested_by": None, "path": ["T"], "components": {}}
    stats = {"attempted": 6, "solved": 6, "avg_attempts": 1.0, "days_since_last": 1,
             "coverage_pct": 100, "total_problems": 6}
    assert explain_focus(focus, stats) == "T (score 0.1): it is the next best option by score."


@pytest.mark.parametrize(
    "attempted, solved, expected",
    [
        (5, 2, "X (score 0.3): you solved 2 of 5 problems tried (40%)."),
        (4, 2, "X (score 0.3): you solved 2 of 4 problems tried (50%). "
               "Only 4 problems tried so far, so treat this as a rough signal."),
    ],
)
def test_small_sample_warning_applies_below_five_problems(attempted, solved, expected):
    focus = {"topic": "X", "score": 0.3, "requested_by": None, "path": ["X"],
             "components": {"low_solve": 0.3, "struggle": 0.0, "staleness": 0.0, "coverage_gap": 0.0}}
    stats = {"attempted": attempted, "solved": solved, "avg_attempts": 2.0, "days_since_last": 10,
             "coverage_pct": 100, "total_problems": attempted}
    assert explain_focus(focus, stats) == expected


def test_equal_contributions_follow_the_fixed_signal_order():
    focus = {"topic": "T", "score": 0.3, "requested_by": None, "path": ["T"],
             "components": {"low_solve": 0.1, "struggle": 0.1, "staleness": 0.1, "coverage_gap": 0.0}}
    stats = {"attempted": 6, "solved": 3, "avg_attempts": 2.0, "days_since_last": 5,
             "coverage_pct": 100, "total_problems": 6}
    assert explain_focus(focus, stats) == (
        "T (score 0.3): you solved 3 of 6 problems tried (50%) and it takes about 2.0 attempts per problem."
    )


def test_new_problem_at_the_target_level_that_also_covers_the_requesting_topic():
    focus = {"topic": "Stacks & Queues", "requested_by": "Graphs"}
    problem = {"title": "Rotting Oranges", "difficulty": "Medium", "topics": "Graphs|Stacks & Queues"}
    assert explain_new_problem(problem, "Medium", focus) == (
        "Rotting Oranges: new Medium problem in Stacks & Queues; matches your target level "
        "(Medium). It also covers Graphs, so it advances both."
    )


def test_new_problem_off_the_target_level():
    focus = {"topic": "Stacks & Queues", "requested_by": "Graphs"}
    problem = {"title": "Implement Queue using Stacks", "difficulty": "Easy", "topics": "Stacks & Queues"}
    assert explain_new_problem(problem, "Medium", focus) == (
        "Implement Queue using Stacks: new Easy problem in Stacks & Queues; closest untouched "
        "match to your target level (Medium)."
    )


def test_new_problem_that_does_not_cover_the_requesting_topic():
    focus = {"topic": "Stacks & Queues", "requested_by": "Graphs"}
    problem = {"title": "X", "difficulty": "Medium", "topics": "Stacks & Queues"}
    assert explain_new_problem(problem, "Medium", focus) == (
        "X: new Medium problem in Stacks & Queues; matches your target level (Medium)."
    )


def test_review_with_several_attempts():
    review = {"title": "Maximum Subarray", "status": "Needs Revision", "attempts": 3,
              "days_ago": 10, "interval_days": 3, "overdue_days": 7}
    assert explain_review(review) == (
        "Maximum Subarray: last result was Needs Revision after 3 attempts, 10 days ago; "
        "due after 3 days, so 7 days overdue."
    )


def test_review_with_a_single_attempt_uses_the_singular():
    review = {"title": "Two Sum", "status": "Solved", "attempts": 1,
              "days_ago": 40, "interval_days": 30, "overdue_days": 10}
    assert explain_review(review) == (
        "Two Sum: last result was Solved after 1 attempt, 40 days ago; "
        "due after 30 days, so 10 days overdue."
    )
