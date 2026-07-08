import { useCallback, useEffect, useState } from 'react'
import { fetchHistory, resetConversation } from '../api/client'
import type { ChatMessage } from '../types'

function errorMessage(err: unknown, fallback: string): string {
  return err instanceof Error && err.message ? err.message : fallback
}

interface UseConversationParams {
  setMessages: (messages: ChatMessage[]) => void
  setError: (message: string | null) => void
  onBeforeReset: () => void
}

export interface UseConversation {
  isLoadingHistory: boolean
  reset: () => Promise<void>
}

export function useConversation({ setMessages, setError, onBeforeReset }: UseConversationParams): UseConversation {
  const [isLoadingHistory, setIsLoadingHistory] = useState(true)

  useEffect(() => {
    let active = true
    fetchHistory()
      .then((res) => active && setMessages(res.messages))
      .catch((err) => active && setError(errorMessage(err, 'Could not load conversation history.')))
      .finally(() => active && setIsLoadingHistory(false))
    return () => {
      active = false
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const reset = useCallback(async () => {
    onBeforeReset()
    setError(null)
    try {
      await resetConversation()
      setMessages([])
    } catch (err) {
      setError(errorMessage(err, 'Could not reset the conversation.'))
    }
  }, [onBeforeReset, setError, setMessages])

  return { isLoadingHistory, reset }
}
