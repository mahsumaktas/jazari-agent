import { useEffect, useRef } from 'react'

interface TranscriptMessage {
  type: string
  content: string
}

interface Props {
  messages: TranscriptMessage[]
}

function formatTimestamp(): string {
  const now = new Date()
  return now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

export function Transcript({ messages }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null)
  const timestampsRef = useRef<Map<number, string>>(new Map())

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Assign timestamps to new messages
  messages.forEach((_, i) => {
    if (!timestampsRef.current.has(i)) {
      timestampsRef.current.set(i, formatTimestamp())
    }
  })

  if (messages.length === 0) {
    return (
      <div role="log" aria-label="Voice transcript" className="bg-jazari-surface rounded-lg p-4">
        <p className="text-jazari-text-dim text-sm text-center">
          Voice transcripts will appear here
        </p>
      </div>
    )
  }

  return (
    <div role="log" aria-label="Voice transcript" className="bg-jazari-surface rounded-lg p-4 max-h-48 overflow-y-auto space-y-2">
      {messages.map((msg, i) => {
        const isUser = msg.content.startsWith('[user]')
        const displayContent = isUser ? msg.content.replace(/^\[user\]\s*/, '') : msg.content
        const timestamp = timestampsRef.current.get(i) || ''

        return (
          <div key={i} className="text-sm flex items-start gap-2" style={{ animation: 'fadeInUp 0.3s ease' }}>
            <span className="text-[10px] text-jazari-text-dim/50 shrink-0 mt-0.5 tabular-nums">
              {timestamp}
            </span>
            <span className={`text-[10px] font-medium uppercase tracking-wider shrink-0 mt-0.5 ${
              isUser ? 'text-jazari-gold' : 'text-jazari-text-dim'
            }`}>
              {isUser ? 'You' : 'Jazari'}
            </span>
            <span className="text-jazari-text">{displayContent}</span>
          </div>
        )
      })}
      <div ref={bottomRef} />
    </div>
  )
}
