import { useState, useRef, useEffect } from 'react'
import type { ChatMessage } from '../hooks/useTextChat'

interface Props {
  messages: ChatMessage[]
  isLoading: boolean
  onSend: (text: string) => void
}

export function TextChat({ messages, isLoading, onSend }: Props) {
  const [input, setInput] = useState('')
  const bottomRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isLoading) return
    onSend(input)
    setInput('')
  }

  return (
    <div className="w-full max-w-lg flex flex-col">
      <div role="log" aria-label="Chat messages" className="max-h-96 overflow-y-auto space-y-3 p-4 bg-jazari-surface rounded-t-lg">
        {messages.length === 0 ? (
          <p className="text-jazari-text-dim text-sm text-center">
            Type a message to start chatting with Jazari
          </p>
        ) : (
          messages.map((msg, i) => (
            <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`} style={{ animation: 'fadeInUp 0.3s ease' }}>
              <div className={`max-w-[80%] px-3 py-2 rounded-lg text-sm ${
                msg.role === 'user'
                  ? 'bg-jazari-gold/20 text-jazari-text'
                  : 'bg-jazari-surface-light text-jazari-text'
              }`}>
                {msg.agent && msg.agent !== 'jazari' && msg.agent !== 'jazari_full' && (
                  <span className="text-jazari-gold text-[10px] font-medium uppercase tracking-wider block mb-1">
                    {msg.agent.replace('_agent', '').replace('_', ' ')}
                  </span>
                )}
                {msg.content.split('\n').map((line, j) => (
                  <span key={j}>
                    {j > 0 && <br />}
                    {line}
                  </span>
                ))}
              </div>
            </div>
          ))
        )}
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-jazari-surface-light px-3 py-2 rounded-lg text-sm text-jazari-text-dim">
              <span className="flex items-center gap-1">
                <span className="w-1.5 h-1.5 bg-jazari-gold rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <span className="w-1.5 h-1.5 bg-jazari-gold rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <span className="w-1.5 h-1.5 bg-jazari-gold rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </span>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <form onSubmit={handleSubmit} className="flex gap-2 p-2 bg-jazari-surface-light rounded-b-lg">
        <input
          ref={inputRef}
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type a message..."
          aria-label="Type a message"
          className="flex-1 bg-jazari-dark text-jazari-text text-sm px-3 py-2 rounded-lg border border-jazari-gold/20 focus:border-jazari-gold focus:outline-none placeholder:text-jazari-text-dim"
          disabled={isLoading}
        />
        <button
          type="submit"
          disabled={isLoading || !input.trim()}
          className="px-4 py-2 bg-jazari-gold text-jazari-dark text-sm font-medium rounded-lg hover:bg-jazari-gold-light disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          Send
        </button>
      </form>
    </div>
  )
}
