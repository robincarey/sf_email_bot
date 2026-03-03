interface StoreToggleProps {
  storeName: string
  enabled: boolean
  onToggle: (enabled: boolean) => void
  disabled?: boolean
}

export default function StoreToggle({ storeName, enabled, onToggle, disabled }: StoreToggleProps) {
  return (
    <div className="flex items-center justify-between py-3">
      <span className="text-sm font-medium text-text">{storeName}</span>
      <button
        role="switch"
        aria-checked={enabled}
        disabled={disabled}
        onClick={() => onToggle(!enabled)}
        className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand disabled:opacity-50 disabled:cursor-not-allowed ${
          enabled ? 'bg-brand' : 'bg-gray-200 dark:bg-gray-600'
        }`}
      >
        <span
          className={`pointer-events-none inline-block h-5 w-5 rounded-full bg-white shadow ring-0 transition-transform duration-200 ${
            enabled ? 'translate-x-5' : 'translate-x-0'
          }`}
        />
      </button>
    </div>
  )
}
