from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Conversation, Message


class ConversationRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_current_conversation(self) -> Conversation:
        result = await self._session.execute(
            select(Conversation).order_by(Conversation.id.desc()).limit(1)
        )
        conversation = result.scalar_one_or_none()
        if conversation is None:
            conversation = await self._create_conversation()
        return conversation

    async def reset_conversation(self) -> Conversation:
        return await self._create_conversation()

    async def list_messages(self, conversation_id: int) -> list[Message]:
        result = await self._session.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.id.asc())
        )
        return list(result.scalars().all())

    async def add_message(
        self,
        conversation_id: int,
        role: str,
        content: str,
        tool_name: str | None = None,
        tool_call_id: str | None = None,
    ) -> Message:
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            tool_name=tool_name,
            tool_call_id=tool_call_id,
        )
        self._session.add(message)
        await self._session.commit()
        await self._session.refresh(message)
        return message

    async def _create_conversation(self) -> Conversation:
        conversation = Conversation()
        self._session.add(conversation)
        await self._session.commit()
        await self._session.refresh(conversation)
        return conversation
