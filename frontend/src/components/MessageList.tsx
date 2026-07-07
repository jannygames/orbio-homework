import { useAutoScroll } from '../hooks/useAutoScroll'
import type { ChatMessage } from '../types'
import { MessageBubble } from './MessageBubble'
import { ToolActivity } from './ToolActivity'
import { TypingIndicator } from './TypingIndicator'

function isToolRow(message: ChatMessage) {
  return message.role === 'tool_call' || message.role === 'tool_result'
}

function shouldShowTyping(messages: ChatMessage[], isStreaming: boolean) {
  if (!isStreaming) return false
  const last = messages[messages.length - 1]
  if (!last) return true
  if (last.role === 'assistant' && last.content.length > 0) return false
  return true
}

export function MessageList({
  messages,
  isStreaming,
}: {
  messages: ChatMessage[]
  isStreaming: boolean
}) {
  const scrollRef = useAutoScroll<HTMLDivElement>([messages, isStreaming])

  return (
    <div ref={scrollRef} className="scroll-slim flex-1 space-y-3 overflow-y-auto px-4 py-5 sm:px-6">
      {messages.map((message) =>
        isToolRow(message) ? (
          <ToolActivity key={message.id} message={message} />
        ) : (
          <MessageBubble key={message.id} message={message} />
        ),
      )}
      {shouldShowTyping(messages, isStreaming) && <TypingIndicator />}
    </div>
  )
}
