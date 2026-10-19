import pytest

pytestmark = pytest.mark.integration

# topic: number of problems tagged with it (these add up to the 139 problem-topic links)
PROBLEMS_PER_TOPIC = {
    "Arrays": 28, "Strings": 12, "Hashing": 10, "Recursion": 10, "Dynamic Programming": 10,
    "Two Pointers": 8, "Sorting": 8, "Stacks & Queues": 7, "Heaps": 7, "Binary Search": 6,
    "Trees": 6, "Backtracking": 6, "Greedy": 6, "Sliding Window": 5, "Linked Lists": 5,
    "Graphs": 5,
}
UNTOUCHED = {
    "Best Time to Buy and Sell Stock", "Climbing Stairs", "Implement Queue using Stacks",
    "Linked List Cycle", "Maximum Average Subarray I", "Binary Tree Level Order Traversal",
    "Coin Change", "Longest Substring Without Repeating Characters", "Merge Intervals",
    "Rotting Oranges", "Search in Rotated Sorted Array", "Sort Colors", "N-Queens",
}


def get(client, path, **params):
    return client.get(path, params=params)


def titles(client, **params):
    params.setdefault("limit", 100)
    response = get(client, "/problems", **params)
    assert response.status_code == 200, response.text
    return [p["title"] for p in response.json()["items"]]


def total(client, **params):
    response = get(client, "/problems", **params)
    assert response.status_code == 200, response.text
    return response.json()["total"]


# ---------- health and docs ----------

def test_health_reports_the_seeded_data(client):
    response = get(client, "/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "connected", "submissions": 72}


def test_openapi_lists_every_endpoint(client):
    paths = set(get(client, "/openapi.json").json()["paths"])
    assert paths >= {"/health", "/topics", "/topics/stats", "/problems",
                     "/submissions", "/recommendations", "/reviews/due"}


# ---------- /topics ----------

def test_topics_are_complete_and_alphabetical(client):
    topics = get(client, "/topics").json()
    names = [t["name"] for t in topics]
    assert len(topics) == 16
    assert names == sorted(names)
    assert names[0] == "Arrays" and names[-1] == "Two Pointers"


def test_topic_item_shape(client):
    assert set(get(client, "/topics").json()[0]) == {"topic_id", "name"}


# ---------- /topics/stats ----------

@pytest.mark.parametrize(
    "topic, total_problems, attempted, solved",
    [("Arrays", 28, 23, 17), ("Graphs", 5, 4, 1), ("Heaps", 7, 7, 6), ("Stacks & Queues", 7, 4, 2)],
)
def test_topic_stats_known_values(client, topic, total_problems, attempted, solved):
    rows = {r["topic"]: r for r in get(client, "/topics/stats").json()}
    assert len(rows) == 16
    row = rows[topic]
    assert (row["total_problems"], row["attempted"], row["solved"]) == (total_problems, attempted, solved)


def test_topic_stats_are_internally_consistent(client):
    for row in get(client, "/topics/stats").json():
        assert 0 <= row["solved"] <= row["attempted"] <= row["total_problems"], row
        assert abs(row["coverage_pct"] - 100 * row["attempted"] / row["total_problems"]) <= 0.51, row
        assert abs(row["solve_pct"] - 100 * row["solved"] / row["attempted"]) <= 0.51, row
        assert row["days_since_last"] >= 0


# ---------- /problems: paging and shape ----------

def test_default_page(client):
    page = get(client, "/problems").json()
    assert (page["total"], page["limit"], page["offset"], len(page["items"])) == (72, 50, 0, 50)


def test_problem_item_shape_and_first_problem(client):
    first = get(client, "/problems").json()["items"][0]
    assert set(first) == {"problem_id", "title", "difficulty", "topics", "latest_status"}
    assert first["problem_id"] == 1 and first["title"] == "Two Sum"
    assert first["difficulty"] == "Easy"
    assert first["topics"] == ["Arrays", "Hashing"]
    assert first["latest_status"] == "Solved"


def test_problems_are_ordered_by_id(client):
    ids = [p["problem_id"] for p in get(client, "/problems", limit=100).json()["items"]]
    assert ids == sorted(ids)


@pytest.mark.parametrize(
    "limit, offset, expected",
    [(50, 0, 50), (50, 50, 22), (10, 70, 2), (10, 72, 0), (100, 0, 72), (1, 0, 1)],
)
def test_paging(client, limit, offset, expected):
    page = get(client, "/problems", limit=limit, offset=offset).json()
    assert page["total"] == 72
    assert (page["limit"], page["offset"], len(page["items"])) == (limit, offset, expected)


def test_pages_cover_every_problem_exactly_once(client):
    everything = [p["problem_id"] for p in get(client, "/problems", limit=100).json()["items"]]
    pages = []
    for offset in (0, 25, 50):
        pages += [p["problem_id"] for p in get(client, "/problems", limit=25, offset=offset).json()["items"]]
    assert pages == everything
    assert len(set(pages)) == 72


# ---------- /problems: filters ----------

@pytest.mark.parametrize(
    "status, expected",
    [("Solved", 43), ("Attempted", 10), ("Needs Revision", 6), ("Untouched", 13)],
)
def test_status_filter_counts(client, status, expected):
    assert total(client, status=status) == expected


def test_status_filters_partition_the_problems(client):
    counts = [total(client, status=s) for s in ("Solved", "Attempted", "Needs Revision", "Untouched")]
    assert sum(counts) == 72


def test_untouched_problems_are_exactly_the_known_thirteen(client):
    names = titles(client, status="Untouched")
    assert set(names) == UNTOUCHED and len(names) == 13
    items = get(client, "/problems", status="Untouched", limit=100).json()["items"]
    assert all(p["latest_status"] is None for p in items)


@pytest.mark.parametrize(
    "title, status",
    [
        ("Maximum Subarray", "Needs Revision"),
        ("Container With Most Water", "Attempted"),
        ("Two Sum", "Solved"),
        ("Rotting Oranges", "Untouched"),
    ],
)
def test_latest_status_of_named_problems(client, title, status):
    assert title in titles(client, status=status)


@pytest.mark.parametrize("difficulty, expected", [("Easy", 19), ("Medium", 42), ("Hard", 11)])
def test_difficulty_filter_counts(client, difficulty, expected):
    assert total(client, difficulty=difficulty) == expected


@pytest.mark.parametrize("topic, expected", PROBLEMS_PER_TOPIC.items())
def test_topic_filter_counts(client, topic, expected):
    page = get(client, "/problems", topic=topic, limit=100).json()
    assert page["total"] == expected
    assert all(topic in p["topics"] for p in page["items"])


@pytest.mark.parametrize("spelling", ["graphs", "GRAPHS", "GrApHs"])
def test_topic_filter_ignores_case(client, spelling):
    page = get(client, "/problems", topic=spelling).json()
    assert page["total"] == 5
    assert all("Graphs" in p["topics"] for p in page["items"])


@pytest.mark.parametrize(
    "params, expected",
    [
        ({"topic": "Graphs", "status": "Untouched"}, ["Rotting Oranges"]),
        ({"topic": "Dynamic Programming", "difficulty": "Hard"}, ["Edit Distance"]),
        ({"topic": "Heaps", "status": "Untouched"}, []),     # Heaps is fully covered
    ],
    ids=["graphs-untouched", "dp-hard", "heaps-untouched"],
)
def test_filters_combine(client, params, expected):
    assert titles(client, **params) == expected


# ---------- errors ----------

@pytest.mark.parametrize(
    "params, code",
    [
        ({"topic": "Nope"}, 404),
        ({"difficulty": "Impossible"}, 422),
        ({"status": "Done"}, 422),
        ({"limit": 0}, 422),
        ({"limit": 101}, 422),
        ({"offset": -1}, 422),
        ({"limit": "abc"}, 422),
    ],
    ids=["unknown-topic", "bad-difficulty", "bad-status", "limit-0", "limit-101",
         "negative-offset", "limit-not-a-number"],
)
def test_bad_requests_are_rejected(client, params, code):
    assert get(client, "/problems", **params).status_code == code


def test_the_largest_allowed_limit_is_accepted(client):
    assert get(client, "/problems", limit=100).status_code == 200
