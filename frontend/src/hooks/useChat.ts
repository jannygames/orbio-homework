import { useCallback, useEffect, useRef, useState } from 'react'
import { fetchHistory, resetConversation, streamChat, type StreamEvent } from '../api/client'
import type { ChatMessage, MessageRole } from '../types'

let tempIdSeq = -1
const nextTempId = () => tempIdSeq--

function makeMessage(role: MessageRole, content: string, toolName: string | null = null): ChatMessage {
  return { id: nextTempId(), role, content, tool_name: toolName, created_at: new Date().toISOString() }
}

function errorMessage(err: unknown, fallback: string): string {
  return err instanceof Error && err.message ? err.message : fallback
}

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
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [isStreaming, setIsStreaming] = useState(false)
  const [isLoadingHistory, setIsLoadingHistory] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const abortRef = useRef<AbortController | null>(null)

  useEffect(() => {
    let active = true
    fetchHistory()
      .then((res) => active && setMessages(res.messages))
      .catch((err) => active && setError(errorMessage(err, 'Could not load conversation history.')))
      .finally(() => active && setIsLoadingHistory(false))
    return () => {
      active = false
      abortRef.current?.abort()
    }
  }, [])

  const sendMessage = useCallback(
    (text: string) => {
      const trimmed = text.trim()
      if (!trimmed || isStreaming) return

      setError(null)
      setMessages((prev) => [...prev, makeMessage('user', trimmed)])

      const controller = new AbortController()
      abortRef.current = controller
      setIsStreaming(true)

      let assistantId: number | null = null
      let assistantText = ''

      const writeAssistant = () => {
        setMessages((prev) => {
          if (assistantId === null) {
            const draft = makeMessage('assistant', assistantText)
            assistantId = draft.id
            return [...prev, draft]
          }
          return prev.map((m) => (m.id === assistantId ? { ...m, content: assistantText } : m))
        })
      }

      const handleEvent = (event: StreamEvent) => {
        switch (event.event) {
          case 'token':
            assistantText += (event.data.text as string) ?? ''
            writeAssistant()
            break
          case 'tool_call':
            setMessages((prev) => [
              ...prev,
              makeMessage('tool_call', JSON.stringify(event.data.args ?? {}), event.data.tool as string),
            ])
            break
          case 'tool_result':
            setMessages((prev) => [
              ...prev,
              makeMessage('tool_result', JSON.stringify(event.data.result ?? {}), event.data.tool as string),
            ])
            break
          case 'error':
            setError((event.data.message as string) ?? 'Something went wrong.')
            break
          case 'done':
            if (assistantId === null && !assistantText.trim()) {
              setMessages((prev) => [
                ...prev,
                makeMessage('assistant', "I'm not sure how to help with that. Try asking about our products."),
              ])
            }
            break
        }
      }

      streamChat(trimmed, handleEvent, controller.signal)
        .catch((err) => {
          if (controller.signal.aborted) return
          setError(errorMessage(err, 'The assistant failed to respond. Please try again.'))
        })
        .finally(() => {
          if (abortRef.current === controller) abortRef.current = null
          setIsStreaming(false)
        })
    },
    [isStreaming],
  )

  const stop = useCallback(() => {
    abortRef.current?.abort()
    setIsStreaming(false)
  }, [])

  const reset = useCallback(async () => {
    abortRef.current?.abort()
    setError(null)
    try {
      await resetConversation()
      setMessages([])
    } catch (err) {
      setError(errorMessage(err, 'Could not reset the conversation.'))
    }
  }, [])

  const dismissError = useCallback(() => setError(null), [])

  return { messages, isStreaming, isLoadingHistory, error, sendMessage, reset, stop, dismissError }
}
