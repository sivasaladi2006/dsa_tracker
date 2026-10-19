import logging
from unittest.mock import MagicMock, patch

import pymysql
import pytest

pytestmark = pytest.mark.integration

REQUESTS = {
    "health": ("get", "/health", {}),
    "topics": ("get", "/topics", {}),
    "topic-stats": ("get", "/topics/stats", {}),
    "problems": ("get", "/problems", {}),
    "problems-by-topic": ("get", "/problems", {"params": {"topic": "graphs"}}),
    "submissions-list": ("get", "/submissions", {}),
    "submissions-create": ("post", "/submissions", {"json": {"problem_id": 1, "status": "Solved"}}),
    "recommendations": ("get", "/recommendations", {}),
    "reviews-due": ("get", "/reviews/due", {}),
}


def down():
    return pymysql.err.OperationalError(2003, "Can't connect to MySQL server on 'localhost'")


def lost():
    return pymysql.err.OperationalError(2013, "Lost connection to MySQL server during query")


def send(client, method, path, kwargs):
    return getattr(client, method)(path, **kwargs)


def failing_connection(error):
    conn = MagicMock()
    cursor = conn.cursor.return_value.__enter__.return_value
    cursor.execute.side_effect = error
    return conn


@pytest.mark.parametrize("method, path, kwargs", list(REQUESTS.values()), ids=list(REQUESTS))
def test_database_down_gives_a_clean_503(client, method, path, kwargs):
    with patch("pymysql.connect", side_effect=down()):
        response = send(client, method, path, kwargs)
    assert response.status_code == 503
    assert response.json() == {"detail": "Database unavailable"}
    assert response.headers["retry-after"] == "5"
    assert "localhost" not in response.text and "MySQL" not in response.text


def test_validation_still_works_when_the_database_is_down(client):
    with patch("pymysql.connect", side_effect=down()):
        response = client.post("/submissions", json={"problem_id": 1, "status": "Done"})
    assert response.status_code == 422


def test_api_docs_work_without_the_database(client):
    with patch("pymysql.connect", side_effect=down()):
        assert client.get("/openapi.json").status_code == 200


def test_each_failed_request_is_logged_once(client, caplog):
    with patch("pymysql.connect", side_effect=down()):
        for method, path, kwargs in REQUESTS.values():
            send(client, method, path, kwargs)
    errors = [r for r in caplog.records if r.name == "dsa_tracker" and r.levelno >= logging.ERROR]
    assert len(errors) == len(REQUESTS)
    assert all("Database unavailable" in r.getMessage() for r in errors)
    assert any("/topics/stats" in r.getMessage() for r in errors)


def test_other_database_errors_give_a_500_without_details(client, caplog):
    bad_sql = pymysql.err.ProgrammingError(1064, "You have an error in your SQL syntax near 'secret'")
    with patch("pymysql.connect", side_effect=bad_sql):
        response = client.get("/topics")
    assert response.status_code == 500
    assert response.json() == {"detail": "Database error"}
    assert "secret" not in response.text
    assert len([r for r in caplog.records if r.name == "dsa_tracker"]) == 1


def test_connection_lost_mid_query_gives_503_and_closes_the_connection(client):
    conn = failing_connection(lost())
    with patch("pymysql.connect", return_value=conn):
        response = client.get("/topics")
    assert response.status_code == 503
    assert response.json() == {"detail": "Database unavailable"}
    conn.close.assert_called()


def test_a_failed_write_is_rolled_back(client):
    conn = failing_connection(lost())
    with patch("pymysql.connect", return_value=conn):
        response = client.post("/submissions", json={"problem_id": 1, "status": "Solved"})
    assert response.status_code == 503
    conn.rollback.assert_called()
    conn.commit.assert_not_called()


def test_an_unexpected_bug_gives_a_generic_500(client, caplog):
    with patch("app.services.catalog.list_topics", side_effect=RuntimeError("secret internal detail")):
        response = client.get("/topics")
    assert response.status_code == 500
    assert response.json() == {"detail": "Internal server error"}
    assert "secret" not in response.text
    records = [r for r in caplog.records if r.name == "dsa_tracker"]
    assert len(records) == 1 and records[0].exc_info is not None


def test_the_api_works_normally_after_the_failures(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["submissions"] == 72


def test_a_problem_removed_between_the_check_and_the_insert_gives_404(client):
    conn = MagicMock()
    cursor = conn.cursor.return_value.__enter__.return_value
    cursor.fetchone.return_value = {"1": 1}      # the existence check finds the problem

    def execute(sql, params=None):
        if sql.lstrip().upper().startswith("INSERT"):
            raise pymysql.err.IntegrityError(1452, "Cannot add or update a child row")

    cursor.execute.side_effect = execute
    with patch("pymysql.connect", return_value=conn):
        response = client.post("/submissions", json={"problem_id": 1, "status": "Solved"})
    assert response.status_code == 404
    assert response.json() == {"detail": "Unknown problem_id: 1"}
    conn.rollback.assert_called()
    conn.commit.assert_not_called()
