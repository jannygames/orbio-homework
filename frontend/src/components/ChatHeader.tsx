import { RefreshIcon, SparkIcon } from './icons'

export function ChatHeader({ onReset, disabled }: { onReset: () => void; disabled: boolean }) {
  return (
    <header className="flex items-center justify-between gap-3 border-b border-softgray bg-paper/90 px-4 py-3 backdrop-blur sm:px-5">
      <div className="flex items-center gap-3">
        <span className="flex h-10 w-10 items-center justify-center rounded-default bg-brand text-paper shadow-sm">
          <SparkIcon width={22} height={22} />
        </span>
        <div className="leading-tight">
          <h1 className="text-[15px] font-medium text-ink">
            Product Assistant
          </h1>
          <p className="text-xs text-mutedtext">by Daniel Jankovskij</p>
        </div>
      </div>

      <button
        type="button"
        onClick={onReset}
        disabled={disabled}
        className="inline-flex items-center gap-1.5 rounded-default border-b-[3px] border-b-brand-dark bg-softgray px-3 py-1.5 text-sm font-medium text-brand-dark transition-all duration-300 hover:-translate-y-0.5 hover:border-b-ink hover:bg-brand-dark hover:text-paper disabled:cursor-not-allowed disabled:opacity-40 disabled:hover:translate-y-0"
      >
        <RefreshIcon width={16} height={16} />
        <span className="hidden sm:inline">New chat</span>
      </button>
    </header>
  )
}
