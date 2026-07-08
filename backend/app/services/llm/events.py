from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class EventType(StrEnum):
    TOKEN = "token"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    DONE = "done"
    ERROR = "error"


@dataclass
class ChatEvent:
    event: EventType
    data: dict[str, Any]
