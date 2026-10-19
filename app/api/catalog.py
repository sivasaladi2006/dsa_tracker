from typing import Literal, Optional

from fastapi import APIRouter, HTTPException, Query

from app.schemas import Difficulty, ProblemPage, Topic, TopicStats
from app.services import catalog
from app.services.stats import topic_stats

router = APIRouter()

ProblemStatus = Literal["Solved", "Attempted", "Needs Revision", "Untouched"]


@router.get("/topics", response_model=list[Topic], tags=["topics"])
def get_topics():
    """All topics, alphabetical."""
    return catalog.list_topics()


@router.get("/topics/stats", response_model=list[TopicStats], tags=["topics"])
def get_topic_stats():
    """Per-topic performance: attempted, solved, solve rate, coverage, recency."""
    return topic_stats()


@router.get("/problems", response_model=ProblemPage, tags=["problems"])
def get_problems(
    topic: Optional[str] = Query(None, description="Topic name, case-insensitive"),
    difficulty: Optional[Difficulty] = None,
    status: Optional[ProblemStatus] = Query(
        None, description="Latest submission status, or Untouched for never attempted"
    ),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """Problems with their topics and latest status. Filters can be combined."""
    topic_name = None
    if topic:
        topic_name = catalog.find_topic(topic)
        if topic_name is None:
            raise HTTPException(status_code=404, detail=f"Unknown topic: {topic}")
    return catalog.list_problems(topic_name, difficulty, status, limit, offset)
