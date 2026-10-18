import random

from app.services.scoring import WEIGHTS, smoothed_solve_rate, weakness_score


def close(a, b, tol=0.001):
    return abs(a - b) <= tol


GRAPHS = {"attempted": 4, "solved": 1, "avg_attempts": 2.6, "days_since_last": 35, "coverage_pct": 80}
TREES = {"attempted": 5, "solved": 5, "avg_attempts": 1.7, "days_since_last": 11, "coverage_pct": 83}
DP = {"attempted": 8, "solved": 4, "avg_attempts": 2.0, "days_since_last": 22, "coverage_pct": 80}
STACKS = {"attempted": 4, "solved": 2, "avg_attempts": 2.3, "days_since_last": 6, "coverage_pct": 57}
NEVER = {"attempted": 0, "solved": 0, "avg_attempts": None, "days_since_last": None, "coverage_pct": 0}

assert close(sum(WEIGHTS.values()), 1.0)

# Hand-calculated examples
assert close(weakness_score(GRAPHS)["score"], 0.660), weakness_score(GRAPHS)
assert close(weakness_score(TREES)["score"], 0.236), weakness_score(TREES)
assert close(weakness_score(DP)["score"], 0.489), weakness_score(DP)
assert close(weakness_score(STACKS)["score"], 0.440), weakness_score(STACKS)
assert close(weakness_score(NEVER)["score"], 0.630), weakness_score(NEVER)

# Smoothing: little data stays near 60%, lots of data approaches the real rate
assert close(smoothed_solve_rate(0, 0), 0.6)
assert close(smoothed_solve_rate(1, 4), 0.4)
assert close(smoothed_solve_rate(25, 100), 0.26, tol=0.001)

# Components add up to the score
parts = weakness_score(GRAPHS)
assert close(sum(parts["components"].values()), parts["score"])

# Direction checks: worse inputs never lower the score
base = dict(DP)
assert weakness_score({**base, "days_since_last": 40})["score"] >= weakness_score({**base, "days_since_last": 10})["score"]
assert weakness_score({**base, "solved": 2})["score"] >= weakness_score({**base, "solved": 6})["score"]
assert weakness_score({**base, "avg_attempts": 3.0})["score"] >= weakness_score({**base, "avg_attempts": 1.0})["score"]

# Any plausible input stays inside 0-1
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

print("Scoring checks passed")
