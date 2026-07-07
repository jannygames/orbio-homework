export type MessageRole = 'user' | 'assistant' | 'tool_call' | 'tool_result'

export interface ChatMessage {
  id: number
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
