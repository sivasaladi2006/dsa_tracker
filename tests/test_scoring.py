import random

import pytest

from app.services.scoring import WEIGHTS, smoothed_solve_rate, weakness_score, weakness_signals

GRAPHS = {"attempted": 4, "solved": 1, "avg_attempts": 2.6, "days_since_last": 35, "coverage_pct": 80}
TREES = {"attempted": 5, "solved": 5, "avg_attempts": 1.7, "days_since_last": 11, "coverage_pct": 83}
DP = {"attempted": 8, "solved": 4, "avg_attempts": 2.0, "days_since_last": 22, "coverage_pct": 80}
STACKS = {"attempted": 4, "solved": 2, "avg_attempts": 2.3, "days_since_last": 6, "coverage_pct": 57}
NEVER = {"attempted": 0, "solved": 0, "avg_attempts": None, "days_since_last": None, "coverage_pct": 0}
BASE = {"attempted": 8, "solved": 4, "avg_attempts": 2.0, "days_since_last": 22, "coverage_pct": 80}


def test_weights_add_up_to_one():
    assert sum(WEIGHTS.values()) == pytest.approx(1.0)


@pytest.mark.parametrize(
    "solved, attempted, expected",
    [(0, 0, 0.6), (1, 4, 0.4), (2, 4, 3.8 / 7), (10, 10, 11.8 / 13), (25, 100, 26.8 / 103)],
)
def test_smoothed_solve_rate(solved, attempted, expected):
    assert smoothed_solve_rate(solved, attempted) == pytest.approx(expected)


def test_smoothing_trusts_small_samples_less():
    # A perfect record on 1 problem counts for less than a perfect record on 10.
    assert smoothed_solve_rate(1, 1) < smoothed_solve_rate(10, 10) < 1
    # A failing record on 1 problem is lifted more than a failing record on 10.
    assert smoothed_solve_rate(0, 1) > smoothed_solve_rate(0, 10) > 0


def test_signals_for_a_known_topic():
    signals = weakness_signals(GRAPHS)
    assert signals == pytest.approx(
        {"low_solve": 0.6, "struggle": 0.8, "staleness": 1.0, "coverage_gap": 0.2}
    )


@pytest.mark.parametrize(
    "avg_attempts, expected", [(1.0, 0.0), (2.0, 0.5), (3.0, 1.0), (10.0, 1.0), (0.5, 0.0)]
)
def test_struggle_signal_is_clamped(avg_attempts, expected):
    assert weakness_signals({**BASE, "avg_attempts": avg_attempts})["struggle"] == pytest.approx(expected)


@pytest.mark.parametrize("days, expected", [(0, 0.0), (15, 0.5), (30, 1.0), (300, 1.0)])
def test_staleness_signal_is_clamped(days, expected):
    assert weakness_signals({**BASE, "days_since_last": days})["staleness"] == pytest.approx(expected)


@pytest.mark.parametrize(
    "coverage, expected", [(100, 0.0), (50, 0.5), (0, 1.0), (150, 0.0), (-10, 1.0)]
)
def test_coverage_gap_signal_is_clamped(coverage, expected):
    assert weakness_signals({**BASE, "coverage_pct": coverage})["coverage_gap"] == pytest.approx(expected)


def test_missing_values_use_neutral_defaults():
    assert weakness_signals({}) == pytest.approx(
        {"low_solve": 0.4, "struggle": 0.5, "staleness": 1.0, "coverage_gap": 0.0}
    )
    assert weakness_score({})["score"] == pytest.approx(0.48)


@pytest.mark.parametrize(
    "stats, expected",
    [(GRAPHS, 0.660), (TREES, 0.236), (DP, 0.489), (STACKS, 0.440), (NEVER, 0.630)],
)
def test_known_scores(stats, expected):
    assert weakness_score(stats)["score"] == pytest.approx(expected, abs=0.001)


def test_components_are_weighted_points_that_add_up_to_the_score():
    result = weakness_score(GRAPHS)
    assert result["components"] == pytest.approx(
        {"low_solve": 0.27, "struggle": 0.16, "staleness": 0.2, "coverage_gap": 0.03}, abs=0.001
    )
    assert sum(result["components"].values()) == pytest.approx(result["score"], abs=0.002)


@pytest.mark.parametrize(
    "field, worse, better",
    [("days_since_last", 40, 10), ("solved", 2, 6), ("avg_attempts", 3.0, 1.0), ("coverage_pct", 20, 80)],
)
def test_worse_inputs_raise_the_score(field, worse, better):
    assert weakness_score({**BASE, field: worse})["score"] > weakness_score({**BASE, field: better})["score"]


def test_score_stays_between_0_and_1():
    rng = random.Random(1)
    for _ in range(1000):
        attempted = rng.randint(0, 30)
        stats = {
            "attempted": attempted,
            "solved": rng.randint(0, attempted),
            "avg_attempts": rng.choice([None, rng.uniform(1, 6)]),
            "days_since_last": rng.choice([None, rng.randint(0, 200)]),
            "coverage_pct": rng.choice([None, rng.randint(0, 100)]),
        }
        assert 0 <= weakness_score(stats)["score"] <= 1, stats


def test_input_is_not_modified():
    stats = dict(GRAPHS)
    weakness_score(stats)
    assert stats == GRAPHS
