export type MessageRole = 'user' | 'assistant' | 'tool_call' | 'tool_result'

export const StreamEventType = {
  Token: 'token',
  ToolCall: 'tool_call',
  ToolResult: 'tool_result',
  Done: 'done',
  Error: 'error',
} as const

export type StreamEventName = (typeof StreamEventType)[keyof typeof StreamEventType]

export interface ChatMessage {
  id: number | string
  role: MessageRole
  content: string
  tool_name: string | null
  created_at: string
}

export interface HistoryResponse {
  conversation_id: number
  messages: ChatMessage[]
}

export interface ResetResponse {
  conversation_id: number
  created_at: string
}
