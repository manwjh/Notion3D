"""Agent integration adapter — Notion3D has no LLM; agents plug in here."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


class AgentAdapterError(RuntimeError):
    pass


TERMINAL_STATUSES = frozenset(
    {"FINISHED", "FAILED", "CANCELLED", "ERROR", "SUCCEEDED", "DONE"}
)


@dataclass
class AgentProviderInfo:
    id: str
    title: str
    kind: str  # local | cloud
    configured: bool
    ready: bool
    note: str = ""


@dataclass
class AgentSessionHandle:
    provider: str
    session_id: str
    run_id: str
    external_url: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)


class AgentAdapter(ABC):
    id: str
    title: str
    kind: str

    @abstractmethod
    def info(self) -> AgentProviderInfo: ...

    @abstractmethod
    async def start_turn(
        self,
        project_id: str,
        user_content: str,
        *,
        session_id: str | None = None,
        region: str | None = None,
        turn_id: str | None = None,
        latest_version: int | None = None,
        images: list[dict[str, str]] | None = None,
    ) -> AgentSessionHandle: ...

    @abstractmethod
    async def collect_reply(self, handle: AgentSessionHandle) -> str: ...

    @abstractmethod
    async def run_status(self, handle: AgentSessionHandle) -> str: ...

    def is_terminal(self, status: str) -> bool:
        return status.upper() in TERMINAL_STATUSES
