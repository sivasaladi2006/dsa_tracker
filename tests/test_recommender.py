import copy

import pytest

from app.services.recommender import rank_focus_topics

HIGH = {"attempted": 4, "solved": 1, "avg_attempts": 2.6, "days_since_last": 35, "coverage_pct": 80}    # about 0.66
MID = {"attempted": 8, "solved": 4, "avg_attempts": 2.0, "days_since_last": 22, "coverage_pct": 80}     # about 0.49
STRONG = {"attempted": 10, "solved": 10, "avg_attempts": 1.0, "days_since_last": 1, "coverage_pct": 100}  # about 0.05
NEVER = {"attempted": 0, "solved": 0, "avg_attempts": None, "days_since_last": None, "coverage_pct": 0}  # about 0.63
FEW = {"attempted": 2, "solved": 2, "avg_attempts": 1.0, "days_since_last": 1, "coverage_pct": 100}      # about 0.11, but only 2 tried
WORST = {"attempted": 4, "solved": 0, "avg_attempts": 3.0, "days_since_last": 60, "coverage_pct": 20}    # about 0.85


def row(name, stats):
    return {"topic": name, **stats}


def topics(entries):
    return [e["topic"] for e in entries]


def test_highest_score_first_and_mastered_topics_are_skipped():
    out = rank_focus_topics([row("A", STRONG), row("B", MID), row("C", HIGH)], {}, limit=3)
    assert topics(out) == ["C", "B"]
    assert all(e["requested_by"] is None for e in out)


def test_weak_topic_is_redirected_to_its_weak_prerequisite():
    rows = [row("A", STRONG), row("B", MID), row("C", HIGH)]
    out = rank_focus_topics(rows, {"B": ["A"], "C": ["B"]})
    assert topics(out) == ["B"]
    assert out[0]["requested_by"] == "C"
    assert out[0]["path"] == ["C", "B"]


def test_a_chain_collapses_to_the_root_gap():
    rows = [row("A", STRONG), row("B", MID), row("C", MID), row("D", HIGH)]
    out = rank_focus_topics(rows, {"B": ["A"], "C": ["B"], "D": ["C"]})
    assert topics(out) == ["B"]
    assert out[0]["path"] == ["D", "C", "B"]
    assert out[0]["requested_by"] == "D"


def test_never_practiced_topic_is_not_mastered():
    out = rank_focus_topics([row("A", STRONG), row("N", NEVER)], {})
    assert topics(out) == ["N"]


def test_everything_mastered_gives_no_focus():
    assert rank_focus_topics([row("A", STRONG), row("B", STRONG)], {}) == []


def test_limit_is_respected_and_ties_keep_input_order():
    rows = [row(f"X{i}", MID) for i in range(6)]
    out = rank_focus_topics(rows, {}, limit=3)
    assert topics(out) == ["X0", "X1", "X2"]


def test_prerequisite_gap_ranks_ahead_of_the_topic_that_needs_it():
    out = rank_focus_topics([row("A", MID), row("B", HIGH)], {"B": ["A"]})
    assert topics(out) == ["A"]
    assert out[0]["requested_by"] == "B"


def test_a_few_perfect_results_do_not_count_as_mastery():
    # FEW scores well below the mastery line, but only 2 problems were tried.
    out = rank_focus_topics([row("A", FEW)], {})
    assert topics(out) == ["A"]
    assert out[0]["score"] < 0.35


def test_redirect_picks_the_highest_scoring_of_the_nearest_gaps():
    # C is the weakest. Its two direct prerequisites are both unmet; B (0.66) beats A (0.49).
    rows = [row("C", WORST), row("A", MID), row("B", HIGH)]
    out = rank_focus_topics(rows, {"C": ["A", "B"]}, limit=3)
    assert topics(out) == ["B", "A"]
    assert out[0]["requested_by"] == "C"
    assert out[0]["path"] == ["C", "B"]
    assert out[0]["score"] == pytest.approx(0.66, abs=0.001)
    assert out[1]["requested_by"] is None


def test_entries_have_the_expected_shape():
    (entry,) = rank_focus_topics([row("C", HIGH)], {})
    assert set(entry) == {"topic", "score", "components", "requested_by", "path"}
    assert set(entry["components"]) == {"low_solve", "struggle", "staleness", "coverage_gap"}
    assert entry["path"] == ["C"]
    assert entry["requested_by"] is None


def test_empty_input_gives_no_focus():
    assert rank_focus_topics([], {}) == []


def test_input_is_not_modified():
    rows = [row("A", STRONG), row("B", MID), row("C", HIGH)]
    prereqs = {"B": ["A"], "C": ["B"]}
    rows_before, prereqs_before = copy.deepcopy(rows), copy.deepcopy(prereqs)
    rank_focus_topics(rows, prereqs)
    assert rows == rows_before and prereqs == prereqs_before
