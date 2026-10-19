import os
from pathlib import Path

import pymysql
import pytest
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
TEST_DB = "dsa_tracker_test"

# Point the app at the test database before any app code opens a connection.
load_dotenv(ROOT / ".env")
os.environ["DB_NAME"] = TEST_DB


def _load_schema(conn):
    sql = (ROOT / "data" / "schema.sql").read_text()
    sql = "\n".join(line for line in sql.splitlines() if not line.strip().upper().startswith("USE "))
    with conn.cursor() as cur:
        for statement in sql.split(";"):
            if statement.strip():
                cur.execute(statement)
    conn.commit()


@pytest.fixture(scope="session")
def test_database():
    """Create and seed the test database once per test session."""
    assert os.environ["DB_NAME"] == TEST_DB, "Refusing to run tests against a non-test database"

    admin = pymysql.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )
    try:
        with admin.cursor() as cur:
            cur.execute("DROP DATABASE IF EXISTS dsa_tracker_test")
            cur.execute("CREATE DATABASE dsa_tracker_test CHARACTER SET utf8mb4")
        admin.commit()
    finally:
        admin.close()

    from app.db import get_connection

    conn = get_connection()
    try:
        _load_schema(conn)
    finally:
        conn.close()

    from scripts.import_problems import import_problems
    from scripts.import_submissions import import_submissions
    from scripts.seed_prerequisites import seed_prerequisites
    from scripts.seed_topics import seed_topics

    seed_topics()
    seed_prerequisites()
    import_problems()
    import_submissions()
    return TEST_DB


@pytest.fixture(scope="session")
def client(test_database):
    """A test client for the API, backed by the seeded test database."""
    from fastapi.testclient import TestClient

    from app.main import app

    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def restore_submissions(client):
    """Delete any submissions a test adds, whether the test passes or fails."""
    from app.db import get_connection

    def max_id():
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT COALESCE(MAX(submission_id), 0) AS m FROM submissions")
                return cur.fetchone()["m"]
        finally:
            conn.close()

    baseline = max_id()
    yield
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM submissions WHERE submission_id > %s", (baseline,))
        conn.commit()
    finally:
        conn.close()
