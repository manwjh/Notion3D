"""In-process pub/sub for project state SSE (single-process Engine)."""

from __future__ import annotations

import asyncio
from collections import defaultdict


_subscribers: dict[str, list[asyncio.Queue[str]]] = defaultdict(list)


def subscribe(project_id: str) -> asyncio.Queue[str]:
    queue: asyncio.Queue[str] = asyncio.Queue(maxsize=32)
    _subscribers[project_id].append(queue)
    return queue


def unsubscribe(project_id: str, queue: asyncio.Queue[str]) -> None:
    queues = _subscribers.get(project_id)
    if not queues:
        return
    try:
        queues.remove(queue)
    except ValueError:
        return
    if not queues:
        _subscribers.pop(project_id, None)


def notify(project_id: str) -> None:
    for queue in list(_subscribers.get(project_id, [])):
        try:
            queue.put_nowait(project_id)
        except asyncio.QueueFull:
            continue
