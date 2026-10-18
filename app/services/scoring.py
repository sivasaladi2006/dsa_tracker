PRIOR_RATE = 0.6          # neutral solve rate that sparse data is pulled toward
PRIOR_WEIGHT = 3          # worth three imaginary problems at the neutral rate
STRUGGLE_FULL_AT = 3.0    # average attempts at which the struggle signal hits 1.0
STALE_FULL_AT_DAYS = 30   # days since practice at which the staleness signal hits 1.0
NEUTRAL_STRUGGLE = 0.5    # used when a topic has no submissions yet

WEIGHTS = {
    "low_solve": 0.45,
    "struggle": 0.20,
    "staleness": 0.20,
    "coverage_gap": 0.15,
}


def _clamp(x):
    return max(0.0, min(1.0, x))


def smoothed_solve_rate(solved, attempted):
    """Solve rate pulled toward PRIOR_RATE when there is little data."""
    return (solved + PRIOR_RATE * PRIOR_WEIGHT) / (attempted + PRIOR_WEIGHT)


def weakness_signals(stats):
    """Each signal on a 0-1 scale (1 = worst). stats is one row from topic_stats()."""
    attempted = stats.get("attempted") or 0
    solved = stats.get("solved") or 0

    low_solve = 1 - smoothed_solve_rate(solved, attempted)

    avg_attempts = stats.get("avg_attempts")
    if avg_attempts is None:
        struggle = NEUTRAL_STRUGGLE
    else:
        struggle = _clamp((avg_attempts - 1) / (STRUGGLE_FULL_AT - 1))

    days = stats.get("days_since_last")
    staleness = 1.0 if days is None else _clamp(days / STALE_FULL_AT_DAYS)

    coverage_pct = stats.get("coverage_pct")
    coverage_gap = 0.0 if coverage_pct is None else _clamp(1 - coverage_pct / 100)

    return {
        "low_solve": low_solve,
        "struggle": struggle,
        "staleness": staleness,
        "coverage_gap": coverage_gap,
    }


def weakness_score(stats):
    """Return {'score': 0-1, 'components': weighted points per signal}."""
    signals = weakness_signals(stats)
    points = {name: WEIGHTS[name] * value for name, value in signals.items()}
    return {
        "score": round(sum(points.values()), 3),
        "components": {name: round(p, 3) for name, p in points.items()},
    }
