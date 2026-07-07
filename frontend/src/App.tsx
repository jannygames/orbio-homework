import { ChatHeader } from './components/ChatHeader'
import { Composer } from './components/Composer'
import { DotGridBackground } from './components/DotGridBackground'
import { EmptyState } from './components/EmptyState'
import { ErrorBanner } from './components/ErrorBanner'
import { MessageList } from './components/MessageList'
import { useChat } from './hooks/useChat'

export default function App() {
  const { messages, isStreaming, isLoadingHistory, error, sendMessage, reset, stop, dismissError } =
    useChat()

  const showEmptyState = !isLoadingHistory && messages.length === 0

  return (
    <div className="relative flex h-[100dvh] w-full items-stretch justify-center overflow-hidden bg-softgray sm:p-6">
      <DotGridBackground className="hidden sm:block" />

      <main className="relative z-10 flex h-full w-full flex-col overflow-hidden bg-paper shadow-card sm:h-full sm:max-w-2xl sm:rounded-default">
        <ChatHeader onReset={reset} disabled={isStreaming || isLoadingHistory} />

        {error && <ErrorBanner message={error} onDismiss={dismissError} />}

        {isLoadingHistory ? (
          <div className="flex flex-1 items-center justify-center text-sm text-mutedtext">Loading…</div>
        ) : showEmptyState ? (
          <div className="flex-1 overflow-y-auto">
            <EmptyState onPick={sendMessage} />
          </div>
        ) : (
          <MessageList messages={messages} isStreaming={isStreaming} />
        )}

        <Composer onSend={sendMessage} onStop={stop} isStreaming={isStreaming} />
      </main>
    </div>
  )
}
