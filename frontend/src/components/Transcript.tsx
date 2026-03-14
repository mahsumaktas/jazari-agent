import { useEffect, useRef } from 'react'
import type { TranscriptMessage } from '../hooks/useWebSocket'

interface Props {
  messages: TranscriptMessage[]
  partialUser?: string
  partialJazari?: string
}

export function Transcript({ messages, partialUser, partialJazari }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, partialUser, partialJazari])

  if (messages.length === 0 && !partialUser && !partialJazari) {
    return (
      <div role="log" aria-label="Voice transcript" className="bg-jazari-surface rounded-lg p-6 flex flex-col items-center gap-3">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="w-8 h-8 text-jazari-text-dim/30">
          <path d="M12 1a4 4 0 0 0-4 4v7a4 4 0 0 0 8 0V5a4 4 0 0 0-4-4z" />
          <path d="M19 12a7 7 0 0 1-14 0" />
          <line x1="12" y1="19" x2="12" y2="23" />
          <line x1="8" y1="23" x2="16" y2="23" />
        </svg>
        <p className="text-jazari-text-dim text-sm text-center">
          Voice transcripts will appear here
        </p>
        <p className="text-jazari-text-dim/40 text-xs text-center">
          Tap the microphone to start a conversation
        </p>
      </div>
    )
  }

  return (
    <div role="log" aria-label="Voice transcript" className="bg-jazari-surface rounded-lg p-4 max-h-48 overflow-y-auto space-y-2">
      {messages.map((msg, i) => (
        <div key={i} className="text-sm flex items-start gap-2" style={{ animation: 'fadeInUp 0.3s ease' }}>
          <span className="text-[10px] text-jazari-text-dim/50 shrink-0 mt-0.5 tabular-nums">
            {msg.timestamp}
          </span>
          <span className={`text-[10px] font-medium uppercase tracking-wider shrink-0 mt-0.5 ${
            msg.sender === 'user' ? 'text-jazari-gold' : 'text-emerald-400'
          }`}>
            {msg.sender === 'user' ? 'You' : 'Jazari'}
          </span>
          <span className="text-jazari-text">{msg.content}</span>
        </div>
      ))}

      {/* Live partial transcripts — typing indicator */}
      {partialUser && (
        <div className="text-sm flex items-start gap-2 opacity-50">
          <span className="text-[10px] text-jazari-text-dim/50 shrink-0 mt-0.5 tabular-nums">
            {new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </span>
          <span className="text-[10px] font-medium uppercase tracking-wider shrink-0 mt-0.5 text-jazari-gold">
            You
          </span>
          <span className="text-jazari-text italic">{partialUser}...</span>
        </div>
      )}
      {partialJazari && (
        <div className="text-sm flex items-start gap-2 opacity-50">
          <span className="text-[10px] text-jazari-text-dim/50 shrink-0 mt-0.5 tabular-nums">
            {new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </span>
          <span className="text-[10px] font-medium uppercase tracking-wider shrink-0 mt-0.5 text-emerald-400">
            Jazari
          </span>
          <span className="text-jazari-text italic">{partialJazari}...</span>
        </div>
      )}

      <div ref={bottomRef} />
    </div>
  )
}
