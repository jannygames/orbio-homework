import json
import logging

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.api.deps import get_conversation_repository, get_llm_client
from app.repositories.conversation_repository import ConversationRepository
from app.schemas.chat import ChatRequest, ErrorResponse, HistoryResponse, MessageOut, ResetResponse
from app.services.llm_service import LLMClient, run_chat_turn

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])


def _format_sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


@router.post(
    "",
    summary="Send a chat message",
    description=(
        "Sends a user message to the assistant and streams the reply back as "
        "Server-Sent Events (`token`, `tool_call`, `tool_result`, `done`, `error`). "
        "The full conversation history is loaded from the database before every "
        "turn, so the assistant remembers previous messages and prior tool usage."
    ),
    responses={422: {"model": ErrorResponse, "description": "Invalid message"}},
)
async def chat(
    payload: ChatRequest,
    repo: ConversationRepository = Depends(get_conversation_repository),
    llm_client: LLMClient = Depends(get_llm_client),
) -> StreamingResponse:
    conversation = await repo.get_current_conversation()

    async def event_stream():
        try:
            async for event in run_chat_turn(repo, llm_client, conversation.id, payload.message):
                yield _format_sse(event.event, event.data)
        except Exception:
            logger.exception("Chat turn failed for conversation %s", conversation.id)
            yield _format_sse(
                "error", {"message": "The assistant failed to respond. Please try again."}
            )

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@router.post(
    "/reset",
    response_model=ResetResponse,
    summary="Reset the conversation",
    description="Starts a brand new conversation. The assistant will no longer remember anything before this point.",
)
async def reset_chat(
    repo: ConversationRepository = Depends(get_conversation_repository),
) -> ResetResponse:
    conversation = await repo.reset_conversation()
    return ResetResponse(conversation_id=conversation.id, created_at=conversation.created_at)


@router.get(
    "/history",
    response_model=HistoryResponse,
    summary="Get the current conversation history",
)
async def get_history(
    repo: ConversationRepository = Depends(get_conversation_repository),
) -> HistoryResponse:
    conversation = await repo.get_current_conversation()
    messages = await repo.list_messages(conversation.id)
    return HistoryResponse(
        conversation_id=conversation.id,
        messages=[MessageOut.model_validate(m) for m in messages],
    )
