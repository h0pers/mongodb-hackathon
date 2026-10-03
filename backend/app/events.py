"""Live report feed: one MongoDB change stream fanned out to every SSE client."""

import asyncio
import logging

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pymongo.errors import OperationFailure, PyMongoError

from app.db import reports
from app.reports import to_report

log = logging.getLogger("dublinfix")

router = APIRouter()

QUEUE_SIZE = 100
PING_SECONDS = 15
MAX_BACKOFF_SECONDS = 30


class Broadcaster:
    def __init__(self) -> None:
        self._subscribers: set[asyncio.Queue[str | None]] = set()

    def subscribe(self) -> asyncio.Queue[str | None]:
        queue: asyncio.Queue[str | None] = asyncio.Queue(maxsize=QUEUE_SIZE)
        self._subscribers.add(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue[str | None]) -> None:
        self._subscribers.discard(queue)

    def publish(self, message: str) -> None:
        for queue in list(self._subscribers):
            try:
                queue.put_nowait(message)
            except asyncio.QueueFull:
                # A client this far behind is dropped rather than slowing everyone
                # down. None tells its stream to end; EventSource reconnects and the
                # frontend refetches GET /reports.
                self._subscribers.discard(queue)
                while not queue.empty():
                    queue.get_nowait()
                queue.put_nowait(None)


broadcaster = Broadcaster()


async def watch_reports() -> None:
    """Push every new report to the broadcaster. Runs for the app's lifetime."""
    resume_token = None
    backoff = 1
    while True:
        try:
            pipeline = [{"$match": {"operationType": "insert"}}]
            async with await reports.watch(pipeline, resume_after=resume_token) as stream:
                backoff = 1
                async for change in stream:
                    resume_token = stream.resume_token
                    broadcaster.publish(to_report(change["fullDocument"]).model_dump_json())
        except PyMongoError as exc:
            if isinstance(exc, OperationFailure):
                # The server rejected the stream (for example the resume token fell
                # out of the oplog), so resuming from it would fail forever.
                resume_token = None
            log.warning("Report change stream failed, retrying in %ss: %r", backoff, exc)
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, MAX_BACKOFF_SECONDS)


@router.get("/events")
async def events():
    async def stream():
        # Subscribe inside the generator so the finally below always unsubscribes.
        queue = broadcaster.subscribe()
        try:
            while True:
                try:
                    message = await asyncio.wait_for(queue.get(), PING_SECONDS)
                except TimeoutError:
                    # SSE comment line: keeps proxies from closing an idle connection.
                    yield ": ping\n\n"
                    continue
                if message is None:
                    return
                yield f"data: {message}\n\n"
        finally:
            broadcaster.unsubscribe(queue)

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
