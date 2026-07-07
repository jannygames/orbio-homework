from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.config import get_settings

_settings = get_settings()


class ChatRequest(BaseModel):
    message: str = Field(
        ...,
        min_length=1,
        max_length=_settings.max_message_length,
        description="The user's message to the assistant.",
        examples=["What products do you have under 50 EUR?"],
    )

    @field_validator("message")
    @classmethod
    def sanitize(cls, value: str) -> str:
        cleaned = "".join(ch for ch in value if ch in "\t\n" or ord(ch) >= 32)
        cleaned = cleaned.strip()
        if not cleaned:
            raise ValueError("Message must not be empty or whitespace only.")
        return cleaned


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    role: str
    content: str
    tool_name: str | None = None
    created_at: datetime


class HistoryResponse(BaseModel):
    conversation_id: int
    messages: list[MessageOut]


class ResetResponse(BaseModel):
    conversation_id: int
    created_at: datetime


class ErrorResponse(BaseModel):
    detail: str
