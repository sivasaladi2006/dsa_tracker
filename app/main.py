from fastapi import FastAPI

from app.api.catalog import router as catalog_router
from app.api.recommendations import router as recommendations_router
from app.api.submissions import router as submissions_router
from app.db import get_connection
from app.errors import register_error_handlers

app = FastAPI(
    title="DSA Tracker API",
    version="0.1.0",
    description="Tracks DSA practice, computes topic-wise stats, and recommends what to practice next.",
)
register_error_handlers(app)
app.include_router(catalog_router)
app.include_router(submissions_router)
app.include_router(recommendations_router)


@app.get("/health", tags=["system"])
def health():
    """Check that the API is up and can reach the database."""
    conn = get_connection()  # a failure here becomes a 503 via the error handlers
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS n FROM submissions")
            count = cur.fetchone()["n"]
    finally:
        conn.close()
    return {"status": "ok", "database": "connected", "submissions": count}
