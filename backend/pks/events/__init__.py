"""Event-driven pipeline infrastructure.

Publishing an event enqueues one durable job per subscribed pipeline stage;
a worker executes jobs and stages emit follow-up events, forming the
ingestion pipeline. Jobs survive restarts and failures are retried.
"""

from pks.events.bus import PipelineRegistry, StageContext
from pks.events.models import Job, JobStatus
from pks.events.queue import JobQueue
from pks.events.worker import Worker, WorkerThread

__all__ = [
    "Job",
    "JobQueue",
    "JobStatus",
    "PipelineRegistry",
    "StageContext",
    "Worker",
    "WorkerThread",
]
