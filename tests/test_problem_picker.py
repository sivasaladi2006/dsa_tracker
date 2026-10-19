import pytest

from app.services.problem_picker import pick_problems, suggest_new_problems, target_difficulty

CANDS = [
    {"problem_id": 1, "title": "E1", "difficulty": "Easy", "topics": "T"},
    {"problem_id": 2, "title": "M1", "difficulty": "Medium", "topics": "T"},
    {"problem_id": 3, "title": "H1", "difficulty": "Hard", "topics": "T"},
    {"problem_id": 4, "title": "M2", "difficulty": "Medium", "topics": "T|B"},
]


def ids(problems):
    return [p["problem_id"] for p in problems]


@pytest.mark.parametrize(
    "solved, attempted, expected",
    [
        (0, 0, "Medium"),    # no data: neutral rate 0.60
        (1, 4, "Easy"),      # smoothed 0.40
        (1, 3, "Easy"),      # 0.47
        (2, 4, "Medium"),    # 0.54
        (4, 6, "Medium"),    # 0.64
        (5, 6, "Hard"),      # 0.76
        (3, 3, "Hard"),      # 0.80
        (10, 10, "Hard"),    # 0.91
    ],
)
def test_target_difficulty(solved, attempted, expected):
    assert target_difficulty({"solved": solved, "attempted": attempted}) == expected


def test_target_difficulty_defaults_to_medium_without_stats():
    assert target_difficulty({}) == "Medium"


@pytest.mark.parametrize(
    "target, count, bonus, expected",
    [
        ("Medium", 4, set(), [2, 4, 1, 3]),   # Mediums first; Easy and Hard tie, so id order
        ("Medium", 4, {"B"}, [4, 2, 1, 3]),   # the bonus topic lifts M2 within its distance
        ("Easy", 4, set(), [1, 2, 4, 3]),
        ("Easy", 4, {"B"}, [1, 4, 2, 3]),     # the bonus only reorders within a distance
        ("Hard", 4, set(), [3, 2, 4, 1]),
        ("Medium", 2, set(), [2, 4]),         # count limit
    ],
)
def test_pick_problems_ordering(target, count, bonus, expected):
    assert ids(pick_problems(CANDS, target, count, bonus)) == expected


def test_asking_for_more_than_exist_returns_everything():
    assert len(pick_problems(CANDS, "Medium", 10)) == 4


def test_input_order_does_not_change_the_result():
    assert ids(pick_problems(list(reversed(CANDS)), "Medium", 4)) == [2, 4, 1, 3]


def test_no_candidates():
    assert pick_problems([], "Medium", 3) == []


def test_candidates_are_not_modified():
    before = list(CANDS)
    pick_problems(CANDS, "Hard", 4, {"B"})
    assert CANDS == before


def test_suggestions_for_a_redirected_topic():
    stats = [{"topic": "T", "solved": 2, "attempted": 4}]
    focus = {"topic": "T", "requested_by": "B"}
    other_topic = {"problem_id": 9, "title": "Z", "difficulty": "Easy", "topics": "Other"}
    out = suggest_new_problems(focus, stats, CANDS + [other_topic], count=2)
    assert out["topic"] == "T"
    assert out["target_difficulty"] == "Medium"
    assert ids(out["problems"]) == [4, 2]    # topic Other is excluded; M2 leads via the bonus


def test_suggestions_without_stats_default_to_medium():
    focus = {"topic": "T", "requested_by": None}
    out = suggest_new_problems(focus, [], CANDS, count=1)
    assert out["target_difficulty"] == "Medium"
    assert ids(out["problems"]) == [2]
