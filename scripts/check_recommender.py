from app.services.recommender import rank_focus_topics

HIGH = {"attempted": 4, "solved": 1, "avg_attempts": 2.6, "days_since_last": 35, "coverage_pct": 80}   # about 0.66
MID = {"attempted": 8, "solved": 4, "avg_attempts": 2.0, "days_since_last": 22, "coverage_pct": 80}    # about 0.49
STRONG = {"attempted": 10, "solved": 10, "avg_attempts": 1.0, "days_since_last": 1, "coverage_pct": 100}  # about 0.05
NEVER = {"attempted": 0, "solved": 0, "avg_attempts": None, "days_since_last": None, "coverage_pct": 0}  # about 0.63


def row(name, stats):
    return {"topic": name, **stats}


# 1. No prerequisites: the highest score wins, nothing is redirected
out = rank_focus_topics([row("A", STRONG), row("B", MID), row("C", HIGH)], {}, limit=3)
assert [f["topic"] for f in out] == ["C", "B"], out      # A is mastered, so it is skipped
assert all(f["requested_by"] is None for f in out)

# 2. A weak topic is redirected to its weak prerequisite
rows = [row("A", STRONG), row("B", MID), row("C", HIGH)]
out = rank_focus_topics(rows, {"B": ["A"], "C": ["B"]})
assert len(out) == 1 and out[0]["topic"] == "B", out
assert out[0]["requested_by"] == "C" and out[0]["path"] == ["C", "B"], out

# 3. Chain D -> C -> B -> A (A mastered): everything collapses to the root gap B
rows = [row("A", STRONG), row("B", MID), row("C", MID), row("D", HIGH)]
out = rank_focus_topics(rows, {"B": ["A"], "C": ["B"], "D": ["C"]})
assert len(out) == 1 and out[0]["topic"] == "B", out
assert out[0]["path"] == ["D", "C", "B"] and out[0]["requested_by"] == "D", out

# 4. A never-practiced topic is not mastered and still gets recommended
out = rank_focus_topics([row("A", STRONG), row("N", NEVER)], {})
assert [f["topic"] for f in out] == ["N"], out

# 5. Everything mastered: nothing to recommend
assert rank_focus_topics([row("A", STRONG), row("B", STRONG)], {}) == []

# 6. The limit is respected, and no topic appears twice
rows = [row(f"X{i}", MID) for i in range(6)]
out = rank_focus_topics(rows, {}, limit=3)
assert len(out) == 3 and len({f["topic"] for f in out}) == 3, out

# 7. A weak prerequisite is not recommended ahead of a stronger gap it would hide
rows = [row("A", MID), row("B", HIGH)]
out = rank_focus_topics(rows, {"B": ["A"]})
assert out[0]["topic"] == "A" and out[0]["requested_by"] == "B", out

print("Recommender checks passed")
