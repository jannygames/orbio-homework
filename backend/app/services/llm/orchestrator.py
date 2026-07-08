"""Orchestrates a chat turn: builds model contents, streams the LLM response,
persists conversation state, and drives tool-call execution."""

from __future__ import annotations

import json
import logging
from typing import AsyncIterator
from uuid import uuid4

from google.genai import types

from app.core.config import get_settings
from app.db.models import Message
from app.repositories.conversation_repository import ConversationRepository
from app.services.llm.client import LLMClient
from app.services.llm.events import ChatEvent, EventType
from app.services.llm.prompts import SYSTEM_INSTRUCTION
from app.services.llm.stream import ToolCall
from app.services.product_tools import execute_tool

logger = logging.getLogger(__name__)


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
