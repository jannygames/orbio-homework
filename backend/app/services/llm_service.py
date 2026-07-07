from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Protocol
from uuid import uuid4

from google import genai
from google.genai import types

from app.core.config import get_settings
from app.db.models import Message
from app.repositories.conversation_repository import ConversationRepository
from app.services.product_tools import execute_tool, get_tools

logger = logging.getLogger(__name__)

SYSTEM_INSTRUCTION = (
    "You are a friendly shopping assistant for an online store. "
    "Answer questions about the store's products ONLY using the provided tools - "
    "never invent product names, prices, stock status, ratings or specs. "
    "Available tools: get_products (search/filter), get_product_details (one product), "
    "list_categories (catalog overview), compare_products (side-by-side), and "
    "recommend_products (best-rated within a budget/category). "
    "Pick the most specific tool for the question and call it before answering. "
    "If a question is unrelated to the product catalog, politely say you can only help "
    "with questions about the store's products. Keep answers concise and friendly, cite "
    "concrete numbers (price in EUR, stock, rating) from the tool results, and format "
    "lists of products with short bullet points."
)


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


def build_contents(history: list[Message]) -> list[types.Content]:
    contents: list[types.Content] = []
    index = 0
    total = len(history)
    while index < total:
        msg = history[index]
        if msg.role == "user":
            contents.append(types.Content(role="user", parts=[types.Part.from_text(text=msg.content)]))
            index += 1
        elif msg.role == "assistant":
            contents.append(types.Content(role="model", parts=[types.Part.from_text(text=msg.content)]))
            index += 1
        elif msg.role == "tool_call":
            parts: list[types.Part] = []
            while index < total and history[index].role == "tool_call":
                current = history[index]
                parts.append(
                    types.Part.from_function_call(name=current.tool_name, args=json.loads(current.content))
                )
                index += 1
            contents.append(types.Content(role="model", parts=parts))
        elif msg.role == "tool_result":
            parts = []
            while index < total and history[index].role == "tool_result":
                current = history[index]
                parts.append(
                    types.Part.from_function_response(
                        name=current.tool_name, response=json.loads(current.content)
                    )
                )
                index += 1
            contents.append(types.Content(role="tool", parts=parts))
        else:
            index += 1
    return contents


async def run_chat_turn(
    repo: ConversationRepository,
    llm_client: LLMClient,
    conversation_id: int,
    user_text: str,
) -> AsyncIterator[ChatEvent]:
    max_iterations = get_settings().max_tool_iterations

    await repo.add_message(conversation_id, role="user", content=user_text)
    history = await repo.list_messages(conversation_id)
    contents = build_contents(history)

    for _ in range(max_iterations):
        assistant_text = ""
        tool_calls: list[ToolCall] = []

        async for chunk in llm_client.stream_turn(contents, SYSTEM_INSTRUCTION):
            if chunk.text:
                assistant_text += chunk.text
                yield ChatEvent(EventType.TOKEN, {"text": chunk.text})
            if chunk.tool_calls:
                tool_calls.extend(chunk.tool_calls)

        if not tool_calls:
            await repo.add_message(conversation_id, role="assistant", content=assistant_text)
            yield ChatEvent(EventType.DONE, {"text": assistant_text})
            return

        async for event in _run_tool_calls(repo, conversation_id, contents, tool_calls):
            yield event

    logger.warning(
        "Max tool iterations (%s) reached for conversation %s", max_iterations, conversation_id
    )
    yield ChatEvent(
        EventType.ERROR,
        {"message": "The assistant used too many tool calls without producing an answer."},
    )


async def _run_tool_calls(
    repo: ConversationRepository,
    conversation_id: int,
    contents: list[types.Content],
    tool_calls: list[ToolCall],
) -> AsyncIterator[ChatEvent]:
    contents.append(types.Content(role="model", parts=[call.to_part() for call in tool_calls]))
    call_ids = [str(uuid4()) for _ in tool_calls]
    for call, call_id in zip(tool_calls, call_ids):
        await repo.add_message(
            conversation_id,
            role="tool_call",
            tool_name=call.name,
            tool_call_id=call_id,
            content=json.dumps(call.args),
        )
        yield ChatEvent(EventType.TOOL_CALL, {"tool": call.name, "args": call.args})

    response_parts: list[types.Part] = []
    for call, call_id in zip(tool_calls, call_ids):
        result = execute_tool(call.name, call.args)
        await repo.add_message(
            conversation_id,
            role="tool_result",
            tool_name=call.name,
            tool_call_id=call_id,
            content=json.dumps(result),
        )
        yield ChatEvent(EventType.TOOL_RESULT, {"tool": call.name, "result": result})
        response_parts.append(types.Part.from_function_response(name=call.name, response=result))

    contents.append(types.Content(role="tool", parts=response_parts))
