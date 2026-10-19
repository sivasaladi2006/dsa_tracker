from fastapi import APIRouter, HTTPException, Query

from app.schemas import SubmissionCreate, SubmissionOut
from app.services import submissions

router = APIRouter()


@router.post("/submissions", response_model=SubmissionOut, status_code=201, tags=["submissions"])
def log_submission(body: SubmissionCreate):
    """Log one attempt at a problem."""
    try:
        return submissions.create_submission(body)
    except submissions.ProblemNotFound:
        raise HTTPException(status_code=404, detail=f"Unknown problem_id: {body.problem_id}")


@router.get("/submissions", response_model=list[SubmissionOut], tags=["submissions"])
def get_recent_submissions(limit: int = Query(10, ge=1, le=100)):
    """Newest submissions first."""
    return submissions.recent_submissions(limit)
