import { useCallback, useEffect, useRef, useState } from 'react'
import { streamChat, type StreamEvent } from '../api/client'
import { StreamEventType, type ChatMessage, type MessageRole } from '../types'

function errorMessage(err: unknown, fallback: string): string {
  return err instanceof Error && err.message ? err.message : fallback
}

interface UseChatStreamParams {
  appendMessage: (role: MessageRole, content: string, toolName?: string | null) => ChatMessage
  updateMessage: (id: ChatMessage['id'], content: string) => void
  setError: (message: string | null) => void
}

export interface UseChatStream {
  isStreaming: boolean
  sendMessage: (text: string) => void
  stop: () => void
}

export function useChatStream({ appendMessage, updateMessage, setError }: UseChatStreamParams): UseChatStream {
  const [isStreaming, setIsStreaming] = useState(false)
  const abortRef = useRef<AbortController | null>(null)

  useEffect(() => () => abortRef.current?.abort(), [])

  const stop = useCallback(() => {
    abortRef.current?.abort()
    setIsStreaming(false)
  }, [])

  const sendMessage = useCallback(
    (text: string) => {
      const trimmed = text.trim()
      if (!trimmed || isStreaming) return

      setError(null)
      appendMessage('user', trimmed)

      const controller = new AbortController()
      abortRef.current = controller
      setIsStreaming(true)

      let assistantId: ChatMessage['id'] | null = null
      let assistantText = ''

      const writeAssistant = () => {
        if (assistantId === null) {
          assistantId = appendMessage('assistant', assistantText).id
          return
        }
        updateMessage(assistantId, assistantText)
      }

      const handleEvent = (event: StreamEvent) => {
        switch (event.event) {
          case StreamEventType.Token:
            assistantText += (event.data.text as string) ?? ''
            writeAssistant()
            break
          case StreamEventType.ToolCall:
            appendMessage('tool_call', JSON.stringify(event.data.args ?? {}), event.data.tool as string)
            break
          case StreamEventType.ToolResult:
            appendMessage('tool_result', JSON.stringify(event.data.result ?? {}), event.data.tool as string)
            break
          case StreamEventType.Error:
            setError((event.data.message as string) ?? 'Something went wrong.')
            break
          case StreamEventType.Done:
            if (assistantId === null && !assistantText.trim()) {
              appendMessage('assistant', "I'm not sure how to help with that. Try asking about our products.")
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
    [isStreaming, appendMessage, updateMessage, setError],
  )

  return { isStreaming, sendMessage, stop }
}
