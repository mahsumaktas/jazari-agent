interface Props {
  isConnected: boolean
  isRecording: boolean
  onToggle: () => void
}

export function MicButton({ isConnected, isRecording, onToggle }: Props) {
  return (
    <button
      onClick={onToggle}
      className={`w-24 h-24 rounded-full flex items-center justify-center transition-all duration-300 cursor-pointer ${
        isRecording
          ? 'bg-red-600 shadow-[0_0_40px_rgba(220,38,38,0.5)] scale-110'
          : isConnected
          ? 'bg-jazari-gold hover:bg-jazari-gold-light shadow-[0_0_20px_rgba(197,165,90,0.3)]'
          : 'bg-jazari-surface-light hover:bg-jazari-gold/20'
      }`}
    >
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-10 h-10 text-jazari-dark">
        {isRecording ? (
          <rect x="6" y="6" width="12" height="12" rx="2" />
        ) : (
          <path d="M12 1a4 4 0 0 0-4 4v7a4 4 0 0 0 8 0V5a4 4 0 0 0-4-4zm7 11a7 7 0 0 1-14 0H3a9 9 0 0 0 8 8.94V23h2v-2.06A9 9 0 0 0 21 12h-2z" />
        )}
      </svg>
    </button>
  )
}
