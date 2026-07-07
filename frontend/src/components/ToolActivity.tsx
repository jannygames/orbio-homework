import type { ChatMessage } from '../types'
import { humanizeToolName, summarizeToolPayload } from '../lib/format'
import { CheckIcon, WrenchIcon } from './icons'

export function ToolActivity({ message }: { message: ChatMessage }) {
  const isCall = message.role === 'tool_call'
  const label = message.tool_name ? humanizeToolName(message.tool_name) : 'tool'

  return (
    <div className="flex justify-center px-2">
      <div className="inline-flex max-w-full items-center gap-2 rounded-full bg-paper/70 px-3 py-1 text-xs text-mutedtext shadow-sm">
        <span className={isCall ? 'text-mutedtext' : 'text-brand'}>
          {isCall ? <WrenchIcon width={13} height={13} /> : <CheckIcon width={13} height={13} />}
        </span>
        <span className="font-medium text-ink/70">{label}</span>
        <span className="truncate text-mutedtext">· {summarizeToolPayload(message.content)}</span>
      </div>
    </div>
  )
}
