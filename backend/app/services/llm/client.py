"""LLM client protocol and the concrete Gemini implementation."""

from __future__ import annotations

from typing import AsyncIterator, Protocol

from google import genai
from google.genai import types

from app.services.llm.stream import StreamChunk, ToolCall
from app.services.product_tools import get_tools


class LLMClient(Protocol):
    def stream_turn(
        self,
        contents: list[types.Content],
        system_instruction: str,
    ) -> AsyncIterator[StreamChunk]: ...


class GeminiLLMClient:
    def __init__(self, api_key: str, model: str):
        self._client = genai.Client(api_key=api_key)
        self._model = model

    async def stream_turn(
        self,
        contents: list[types.Content],
        system_instruction: str,
    ) -> AsyncIterator[StreamChunk]:
        config = types.GenerateContentConfig(
            tools=get_tools(),
            system_instruction=system_instruction,
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        )
        stream = await self._client.aio.models.generate_content_stream(
            model=self._model,
            contents=contents,
            config=config,
        )
        async for chunk in stream:
            candidate = chunk.candidates[0] if chunk.candidates else None
            parts = candidate.content.parts if candidate and candidate.content and candidate.content.parts else []

            tool_calls = [
                ToolCall(name=part.function_call.name, args=dict(part.function_call.args or {}), part=part)
                for part in parts
                if part.function_call
            ]
            text_pieces = [p.text for p in parts if p.text and not getattr(p, "thought", False)]
            text = "".join(text_pieces) if text_pieces and not tool_calls else None

            if text or tool_calls:
                yield StreamChunk(text=text, tool_calls=tool_calls)
