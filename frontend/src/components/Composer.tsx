import { useEffect, useLayoutEffect, useRef, useState, type KeyboardEvent } from 'react'
import { SendIcon, StopIcon } from './icons'

const MAX_LENGTH = 2000

export function Composer({
  onSend,
  onStop,
  isStreaming,
}: {
  onSend: (message: string) => void
  onStop: () => void
  isStreaming: boolean
}) {
  const [value, setValue] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const trimmed = value.trim()
  const tooLong = value.length > MAX_LENGTH
  const canSend = trimmed.length > 0 && !tooLong && !isStreaming

  useLayoutEffect(() => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = `${Math.min(el.scrollHeight, 160)}px`
  }, [value])

  useEffect(() => {
    if (!isStreaming) textareaRef.current?.focus()
  }, [isStreaming])

  const submit = () => {
    if (!canSend) return
    onSend(trimmed)
    setValue('')
  }

  const handleKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      submit()
    }
  }

  return (
    <div className="border-t border-softgray bg-paper/90 px-3 py-3 backdrop-blur sm:px-4">
      <div className="flex items-end gap-2 rounded-default border border-softgray bg-paper px-3 py-2 shadow-sm focus-within:border-brand">
        <textarea
          ref={textareaRef}
          rows={1}
          value={value}
          onChange={(event) => setValue(event.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask about a product…"
          aria-label="Message"
          className="max-h-40 flex-1 resize-none bg-transparent py-1 text-sm leading-relaxed text-ink placeholder:text-mutedtext focus:outline-none"
        />

        {isStreaming ? (
          <button
            type="button"
            onClick={onStop}
            aria-label="Stop generating"
            className="flex h-9 w-9 shrink-0 items-center justify-center rounded-default bg-softgray text-ink transition-colors hover:bg-mutedtext/30"
          >
            <StopIcon width={16} height={16} />
          </button>
        ) : (
          <button
            type="button"
            onClick={submit}
            disabled={!canSend}
            aria-label="Send message"
            className="flex h-9 w-9 shrink-0 items-center justify-center rounded-default bg-brand text-paper transition-all duration-300 hover:bg-brand-dark disabled:cursor-not-allowed disabled:opacity-40"
          >
            <SendIcon width={17} height={17} />
          </button>
        )}
      </div>

      <div className="mt-1 flex h-4 items-center justify-between px-1 text-xs">
        <span className="text-red-500">
          {tooLong ? `Message is too long (max ${MAX_LENGTH} characters)` : ''}
        </span>
        <span className={value.length > MAX_LENGTH * 0.9 ? 'text-red-500' : 'text-mutedtext'}>
          {value.length > MAX_LENGTH * 0.75 ? `${value.length}/${MAX_LENGTH}` : ''}
        </span>
      </div>
    </div>
  )
}
