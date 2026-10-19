import pytest

pytestmark = pytest.mark.integration

TITLES = ["Rotting Oranges", "Binary Tree Level Order Traversal", "Implement Queue using Stacks"]


def stats_by_topic(client):
    return {r["topic"]: r for r in client.get("/topics/stats").json()}


def get_plan(client):
    return client.get("/recommendations", params={"focus": 5, "problems": 3, "reviews": 3}).json()


def focus_pairs(plan):
    return [(e["topic"], e["requested_by"]) for e in plan["focus"]]


def untouched(client, **params):
    return client.get("/problems", params={"status": "Untouched", "limit": 100, **params}).json()


@pytest.fixture
def scenario(client, restore_submissions):
    """Log the three Stacks & Queues problems the plan recommends, as solved."""
    before = {"stats": stats_by_topic(client), "plan": get_plan(client)}
    items = untouched(client, topic="Stacks & Queues")["items"]
    assert sorted(p["title"] for p in items) == sorted(TITLES)

    created = []
    for problem in items:
        response = client.post("/submissions", json={
            "problem_id": problem["problem_id"], "status": "Solved",
            "attempts": 1, "time_taken_min": 20})
        assert response.status_code == 201, response.text
        created.append(response.json())

    after = {"stats": stats_by_topic(client), "plan": get_plan(client)}
    return {"before": before, "after": after, "created": created}


def test_before_logging_the_plan_sends_graphs_through_stacks_and_queues(scenario):
    assert ("Stacks & Queues", "Graphs") in focus_pairs(scenario["before"]["plan"])
    assert scenario["before"]["stats"]["Stacks & Queues"]["attempted"] == 4


def test_the_three_recommended_problems_are_saved(client, scenario):
    created = scenario["created"]
    assert sorted(c["title"] for c in created) == sorted(TITLES)
    assert all(c["status"] == "Solved" for c in created)
    recent = client.get("/submissions", params={"limit": 3}).json()
    assert {r["submission_id"] for r in recent} == {c["submission_id"] for c in created}


def test_stats_reflect_the_new_practice(scenario):
    before, after = scenario["before"]["stats"], scenario["after"]["stats"]
    stacks = after["Stacks & Queues"]
    assert (stacks["attempted"], stacks["solved"], stacks["coverage_pct"]) == (7, 5, 100)
    assert stacks["days_since_last"] <= 1          # allows for a run that crosses midnight
    # Rotting Oranges also counts for Graphs, and Level Order Traversal for Trees.
    assert (after["Graphs"]["attempted"], after["Graphs"]["solved"]) == (5, 2)
    assert (after["Trees"]["attempted"], after["Trees"]["solved"]) == (6, 6)
    # A topic none of the three problems belong to is unchanged.
    assert after["Arrays"] == before["Arrays"]


def test_the_untouched_list_shrinks(client, scenario):
    assert untouched(client)["total"] == 10
    assert untouched(client, topic="Stacks & Queues")["total"] == 0
    items = client.get("/problems", params={"limit": 100}).json()["items"]
    status = {p["title"]: p["latest_status"] for p in items}
    assert status["Rotting Oranges"] == "Solved"


def test_the_plan_stops_redirecting_to_stacks_and_queues(scenario):
    after = focus_pairs(scenario["after"]["plan"])
    assert ("Stacks & Queues", "Graphs") not in after
    assert "Stacks & Queues" not in [topic for topic, _ in after]
    assert after != focus_pairs(scenario["before"]["plan"])


def test_solved_problems_are_not_suggested_again(scenario):
    suggested = {p["title"] for e in scenario["after"]["plan"]["focus"] for p in e["new_problems"]}
    assert not suggested & set(TITLES)
