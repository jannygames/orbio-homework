"""Data structures for a single chunk of a streamed LLM response."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from google.genai import types


@dataclass
class ToolCall:
    name: str
    args: dict[str, Any]
    part: types.Part | None = None

    def to_part(self) -> types.Part:
        if self.part is not None:
            return self.part
        return types.Part.from_function_call(name=self.name, args=self.args)


@dataclass
class StreamChunk:
    text: str | None = None
    tool_calls: list[ToolCall] = field(default_factory=list)
