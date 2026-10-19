import os

import pytest

from app.db import get_connection

pytestmark = pytest.mark.integration

EXPECTED_COUNTS = {
    "topics": 16,
    "topic_prerequisites": 20,
    "problems": 72,
    "problem_topics": 139,
    "submissions": 72,
}


def test_app_is_pointed_at_the_test_database():
    assert os.environ["DB_NAME"] == "dsa_tracker_test"


def test_test_database_is_seeded(test_database):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT DATABASE() AS db")
            assert cur.fetchone()["db"] == "dsa_tracker_test"
            for table, expected in EXPECTED_COUNTS.items():
                cur.execute(f"SELECT COUNT(*) AS n FROM {table}")
                assert cur.fetchone()["n"] == expected, table
    finally:
        conn.close()
