from app.services.problem_picker import pick_problems, suggest_new_problems, target_difficulty


def ids(problems):
    return [p["problem_id"] for p in problems]


# Target difficulty from solved / attempted
assert target_difficulty({"solved": 1, "attempted": 4}) == "Easy"      # smoothed 0.40
assert target_difficulty({"solved": 2, "attempted": 4}) == "Medium"    # smoothed 0.54
assert target_difficulty({"solved": 10, "attempted": 10}) == "Hard"    # smoothed 0.91
assert target_difficulty({}) == "Medium"                               # no data: neutral 0.6

CANDS = [
    {"problem_id": 1, "title": "E1", "difficulty": "Easy", "topics": "T"},
    {"problem_id": 2, "title": "M1", "difficulty": "Medium", "topics": "T"},
    {"problem_id": 3, "title": "H1", "difficulty": "Hard", "topics": "T"},
    {"problem_id": 4, "title": "M2", "difficulty": "Medium", "topics": "T|B"},
]

assert ids(pick_problems(CANDS, "Medium", 4)) == [2, 4, 1, 3]                    # Mediums, then Easy/Hard tie by id
assert ids(pick_problems(CANDS, "Medium", 4, {"B"})) == [4, 2, 1, 3]             # bonus topic B lifts M2
assert ids(pick_problems(CANDS, "Easy", 4)) == [1, 2, 4, 3]
assert ids(pick_problems(CANDS, "Easy", 4, {"B"})) == [1, 4, 2, 3]               # bonus only reorders within a distance
assert ids(pick_problems(CANDS, "Hard", 4)) == [3, 2, 4, 1]
assert ids(pick_problems(CANDS, "Medium", 2)) == [2, 4]                          # count limit
assert pick_problems([], "Medium", 3) == []                                      # nothing untouched
assert len(CANDS) == 4 and ids(CANDS) == [1, 2, 3, 4]                            # input not modified

# End to end with a redirected focus entry
stats = [{"topic": "T", "solved": 2, "attempted": 4}]
focus = {"topic": "T", "requested_by": "B"}
out = suggest_new_problems(focus, stats, CANDS + [{"problem_id": 9, "title": "Z", "difficulty": "Easy", "topics": "Other"}], count=2)
assert out["target_difficulty"] == "Medium"
assert ids(out["problems"]) == [4, 2], out        # topic Other is excluded; M2 first via the bonus

print("Problem picker checks passed")
