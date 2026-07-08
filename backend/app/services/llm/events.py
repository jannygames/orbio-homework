"""SSE event types emitted while handling a chat turn."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class EventType:
    """SSE event names emitted during a chat turn."""

    TOKEN = "token"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    DONE = "done"
    ERROR = "error"


@dataclass
class ChatEvent:
    """A single streamable event produced while handling a chat turn."""

    event: str
    data: dict[str, Any]
