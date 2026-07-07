import { AlertIcon, CloseIcon } from './icons'

export function ErrorBanner({ message, onDismiss }: { message: string; onDismiss: () => void }) {
  return (
    <div className="flex items-start gap-2 border-b border-red-100 bg-red-50 px-4 py-2.5 text-sm text-red-700">
      <AlertIcon width={18} height={18} className="mt-0.5 shrink-0" />
      <p className="flex-1">{message}</p>
      <button
        type="button"
        onClick={onDismiss}
        aria-label="Dismiss error"
        className="shrink-0 rounded p-0.5 text-red-400 transition-colors hover:text-red-700"
      >
        <CloseIcon width={16} height={16} />
      </button>
    </div>
  )
}
