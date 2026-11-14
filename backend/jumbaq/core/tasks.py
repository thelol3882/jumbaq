"""Background tasks that services start. The worker runs them (jumbaq.worker)."""

from typing import Any, Protocol

# Names of the worker functions.
DELIVER_OUTBOX = "deliver_outbox"


class TaskQueue(Protocol):
    """The part of ArqRedis that services use, so tests can pass a fake queue."""

    async def enqueue_job(self, function: str, *args: Any, **kwargs: Any) -> Any: ...
