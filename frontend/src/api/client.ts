import { StreamEventType, type HistoryResponse, type ResetResponse, type StreamEventName } from '../types'

const API_BASE = '/api'

async function extractErrorMessage(response: Response, fallback: string): Promise<string> {
  try {
    const body = await response.json()
    return body.detail ?? fallback
  } catch {
    return fallback
  }
}

export async function fetchHistory(): Promise<HistoryResponse> {
  const response = await fetch(`${API_BASE}/chat/history`)
  if (!response.ok) {
    throw new Error(await extractErrorMessage(response, 'Failed to load conversation history.'))
  }
  return response.json()
}

export async function resetConversation(): Promise<ResetResponse> {
  const response = await fetch(`${API_BASE}/chat/reset`, { method: 'POST' })
  if (!response.ok) {
    throw new Error(await extractErrorMessage(response, 'Failed to reset the conversation.'))
  }
  return response.json()
}

export interface StreamEvent {
  event: StreamEventName
  data: Record<string, unknown>
}

export async function streamChat(
  message: string,
  onEvent: (event: StreamEvent) => void,
  signal?: AbortSignal,
): Promise<void> {
  const response = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message }),
    signal,
  })

  if (!response.ok || !response.body) {
    throw new Error(await extractErrorMessage(response, 'The assistant failed to respond.'))
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { value, done } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })

    let boundary = buffer.indexOf('\n\n')
    while (boundary !== -1) {
      const rawEvent = buffer.slice(0, boundary)
      buffer = buffer.slice(boundary + 2)
      boundary = buffer.indexOf('\n\n')

      let eventName: StreamEventName = StreamEventType.Token
      let dataRaw = ''
      for (const line of rawEvent.split('\n')) {
        if (line.startsWith('event:')) {
          eventName = line.slice('event:'.length).trim() as StreamEventName
        } else if (line.startsWith('data:')) {
          dataRaw += line.slice('data:'.length).trim()
        }
      }

      if (dataRaw) {
        try {
          onEvent({ event: eventName, data: JSON.parse(dataRaw) })
        } catch {
          // ignore malformed/partial SSE chunks
        }
      }
    }
  }
}
