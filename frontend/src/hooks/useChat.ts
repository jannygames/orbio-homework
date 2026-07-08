import { useCallback, useState } from 'react'
import type { ChatMessage } from '../types'
import { useChatState } from './useChatState'
import { useChatStream } from './useChatStream'
import { useConversation } from './useConversation'

export interface UseChat {
  messages: ChatMessage[]
  isStreaming: boolean
  isLoadingHistory: boolean
  error: string | null
  sendMessage: (text: string) => void
  reset: () => void
  stop: () => void
  dismissError: () => void
}

export function useChat(): UseChat {
  const [error, setError] = useState<string | null>(null)
  const { messages, setMessages, appendMessage, updateMessage } = useChatState()
  const { isStreaming, sendMessage, stop } = useChatStream({ appendMessage, updateMessage, setError })
  const { isLoadingHistory, reset } = useConversation({ setMessages, setError, onBeforeReset: stop })

  const dismissError = useCallback(() => setError(null), [])

  return { messages, isStreaming, isLoadingHistory, error, sendMessage, reset, stop, dismissError }
}
