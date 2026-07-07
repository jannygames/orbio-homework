import type { ChatMessage } from '../types'
import { Markdown } from './Markdown'

export function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === 'user'

  return (
    <div className={`flex animate-fade-up ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div
        className={
          isUser
            ? 'max-w-[85%] whitespace-pre-wrap break-words rounded-default rounded-br-sm bg-brand px-4 py-2.5 text-sm leading-relaxed text-paper shadow-sm'
            : 'max-w-[85%] break-words rounded-default rounded-bl-sm border border-softgray bg-paper px-4 py-2.5 shadow-sm'
        }
      >
        {isUser ? message.content : <Markdown content={message.content} />}
      </div>
    </div>
  )
}
