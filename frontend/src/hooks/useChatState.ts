import { useCallback, useState } from 'react'
import type { ChatMessage, MessageRole } from '../types'

function makeMessage(role: MessageRole, content: string, toolName: string | null = null): ChatMessage {
  return { id: crypto.randomUUID(), role, content, tool_name: toolName, created_at: new Date().toISOString() }
}

export interface UseChatState {
  messages: ChatMessage[]
  setMessages: (messages: ChatMessage[]) => void
  appendMessage: (role: MessageRole, content: string, toolName?: string | null) => ChatMessage
  updateMessage: (id: ChatMessage['id'], content: string) => void
}

export function useChatState(): UseChatState {
  const [messages, setMessages] = useState<ChatMessage[]>([])

  const appendMessage = useCallback((role: MessageRole, content: string, toolName: string | null = null) => {
    const message = makeMessage(role, content, toolName)
    setMessages((prev) => [...prev, message])
    return message
  }, [])

  const updateMessage = useCallback((id: ChatMessage['id'], content: string) => {
    setMessages((prev) => prev.map((m) => (m.id === id ? { ...m, content } : m)))
  }, [])

  return { messages, setMessages, appendMessage, updateMessage }
}
