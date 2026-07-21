"""Pipeline observability: the global job queue."""

from fastapi import APIRouter, Query
from pydantic import BaseModel

from pks.api.deps import QueueDep
from pks.events.models import Job, JobStatus

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


class JobsOut(BaseModel):
    counts: dict[str, int]
    jobs: list[Job]


@router.get("", response_model=JobsOut)
def list_jobs(
    queue: QueueDep,
    status: JobStatus | None = None,
    limit: int = Query(default=100, ge=1, le=1000),
) -> JobsOut:
    """Most recent pipeline jobs plus per-status counts."""
    return JobsOut(
        counts=queue.counts(),
        jobs=queue.list(status=status, newest_first=True, limit=limit),
    )
