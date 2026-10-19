from fastapi import APIRouter, Query

from app.schemas import Plan, ReviewEntry
from app.services.plan import recommend, review_entries
from app.services.stats import latest_submissions

router = APIRouter()


@router.get("/recommendations", response_model=Plan, tags=["recommendations"])
def get_recommendations(
    focus: int = Query(3, ge=1, le=10, description="Number of focus topics"),
    problems: int = Query(3, ge=1, le=10, description="New problems per topic"),
    reviews: int = Query(3, ge=0, le=20, description="Number of reviews"),
):
    """Today's practice plan: what to focus on, which new problems to try, and what to review."""
    return recommend(focus, problems, reviews)


@router.get("/reviews/due", response_model=list[ReviewEntry], tags=["recommendations"])
def get_due_reviews(limit: int = Query(10, ge=1, le=100)):
    """Problems due for review, unsolved first, then most overdue first."""
    return review_entries(latest_submissions(), limit)
