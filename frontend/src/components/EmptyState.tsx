import { SparkIcon } from './icons'

const SUGGESTIONS = [
  'What products do you have under €50?',
  'Which items are currently on discount?',
  'Do you have any headphones in stock?',
  'Recommend a good gift under €100',
]

export function EmptyState({ onPick }: { onPick: (text: string) => void }) {
  return (
    <div className="flex h-full flex-col items-center justify-center px-6 text-center">
      <span className="mb-4 flex h-14 w-14 items-center justify-center rounded-default bg-brand/10 text-brand-dark">
        <SparkIcon width={28} height={28} />
      </span>
      <h2 className="text-lg font-medium text-ink">How can I help you shop?</h2>
      <p className="mt-1 max-w-sm text-sm text-mutedtext">
        Ask about prices, stock, discounts or how products compare — I look everything up in our
        live catalog.
      </p>

      <div className="mt-6 grid w-full max-w-md grid-cols-1 gap-2 sm:grid-cols-2">
        {SUGGESTIONS.map((suggestion) => (
          <button
            key={suggestion}
            type="button"
            onClick={() => onPick(suggestion)}
            className="rounded-default bg-paper px-4 py-3 text-left text-sm font-medium text-ink shadow-card transition-all duration-300 hover:-translate-y-1 hover:text-brand-dark"
          >
            {suggestion}
          </button>
        ))}
      </div>
    </div>
  )
}
