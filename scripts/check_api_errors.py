import logging
from unittest.mock import MagicMock, patch

import pymysql
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app, raise_server_exceptions=False)


class Collector(logging.Handler):
    def __init__(self):
        super().__init__()
        self.records = []

    def emit(self, record):
        self.records.append(record)


collector = Collector()
logging.getLogger("dsa_tracker").addHandler(collector)

REQUESTS = [
    ("get", "/health", {}),
    ("get", "/topics", {}),
    ("get", "/topics/stats", {}),
    ("get", "/problems", {}),
    ("get", "/problems", {"params": {"topic": "graphs"}}),
    ("get", "/submissions", {}),
    ("post", "/submissions", {"json": {"problem_id": 1, "status": "Solved"}}),
    ("get", "/recommendations", {}),
    ("get", "/reviews/due", {}),
]

# 1. Database down: every endpoint that needs it answers 503, with nothing internal leaked
down = pymysql.err.OperationalError(2003, "Can't connect to MySQL server on 'localhost'")
with patch("pymysql.connect", side_effect=down):
    for method, path, kwargs in REQUESTS:
        r = getattr(client, method)(path, **kwargs)
        assert r.status_code == 503, (method, path, r.status_code, r.text)
        assert r.json() == {"detail": "Database unavailable"}, (path, r.text)
        assert r.headers["retry-after"] == "5", path
        assert "localhost" not in r.text and "MySQL" not in r.text, path
    # Validation happens before the database is touched, and docs need no database
    assert client.post("/submissions", json={"problem_id": 1, "status": "Done"}).status_code == 422
    assert client.get("/openapi.json").status_code == 200

errors = [rec for rec in collector.records if rec.levelno >= logging.ERROR]
assert len(errors) == len(REQUESTS), len(errors)           # one log line per failed request
assert all("Database unavailable" in rec.getMessage() for rec in errors)
assert any("/topics/stats" in rec.getMessage() for rec in errors)

# 2. Another kind of database error: 500, and the SQL message stays out of the response
collector.records.clear()
bad_sql = pymysql.err.ProgrammingError(1064, "You have an error in your SQL syntax near 'secret'")
with patch("pymysql.connect", side_effect=bad_sql):
    r = client.get("/topics")
assert r.status_code == 500 and r.json() == {"detail": "Database error"}, r.text
assert "secret" not in r.text
assert len(collector.records) == 1 and collector.records[0].levelno == logging.ERROR

# 3. The connection drops in the middle of a query: 503, and the connection is still cleaned up
conn = MagicMock()
cursor = conn.cursor.return_value.__enter__.return_value
cursor.execute.side_effect = pymysql.err.OperationalError(2013, "Lost connection to MySQL server during query")
with patch("pymysql.connect", return_value=conn):
    r = client.get("/topics")
assert r.status_code == 503 and r.json() == {"detail": "Database unavailable"}, r.text
conn.close.assert_called()

conn = MagicMock()
cursor = conn.cursor.return_value.__enter__.return_value
cursor.execute.side_effect = pymysql.err.OperationalError(2013, "Lost connection to MySQL server during query")
with patch("pymysql.connect", return_value=conn):
    r = client.post("/submissions", json={"problem_id": 1, "status": "Solved"})
assert r.status_code == 503, r.text
conn.rollback.assert_called()                                # a failed write is rolled back
conn.commit.assert_not_called()

# 4. An unexpected bug: generic 500, the real message only reaches the log
collector.records.clear()
with patch("app.services.catalog.list_topics", side_effect=RuntimeError("secret internal detail")):
    r = client.get("/topics")
assert r.status_code == 500 and r.json() == {"detail": "Internal server error"}, r.text
assert "secret" not in r.text
assert len(collector.records) == 1 and collector.records[0].exc_info is not None

# 5. After all that, the API works normally and nothing was written
r = client.get("/health")
assert r.status_code == 200 and r.json()["submissions"] == 72, r.text

print("Error-handling checks passed")
