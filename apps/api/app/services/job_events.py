"""In-process pub/sub for job status SSE streams (single-process Engine)."""

from __future__ import annotations

import asyncio
from collections import defaultdict


_subscribers: dict[str, list[asyncio.Queue[dict]]] = defaultdict(list)


def subscribe(job_id: str) -> asyncio.Queue[dict]:
    queue: asyncio.Queue[dict] = asyncio.Queue(maxsize=32)
    _subscribers[job_id].append(queue)
    return queue


def unsubscribe(job_id: str, queue: asyncio.Queue[dict]) -> None:
    queues = _subscribers.get(job_id)
    if not queues:
        return
    try:
        queues.remove(queue)
    except ValueError:
        return
    if not queues:
        _subscribers.pop(job_id, None)


def publish(job: dict) -> None:
    job_id = job.get("id")
    if not job_id:
        return
    snapshot = dict(job)
    terminal = job.get("status") in ("succeeded", "failed")
    for queue in list(_subscribers.get(job_id, [])):
        try:
            queue.put_nowait(snapshot)
        except asyncio.QueueFull:
            if not terminal:
                continue
            try:
                while not queue.empty():
                    queue.get_nowait()
            except asyncio.QueueEmpty:
                pass
            try:
                queue.put_nowait(snapshot)
            except asyncio.QueueFull:
                continue
