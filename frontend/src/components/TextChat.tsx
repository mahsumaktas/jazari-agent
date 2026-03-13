import { useState, useRef, useEffect } from 'react'
import type { ChatMessage } from '../hooks/useTextChat'

interface Props {
  messages: ChatMessage[]
  isLoading: boolean
  loadingStatus?: string
  onSend: (text: string) => void
  onPhotoCapture?: (base64: string) => void
}

export function TextChat({ messages, isLoading, loadingStatus, onSend, onPhotoCapture }: Props) {
  const [input, setInput] = useState('')
  const bottomRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const fileRef = useRef<HTMLInputElement>(null)

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
              {loadingStatus ? (
                <span className="text-jazari-gold text-xs animate-pulse">{loadingStatus}</span>
              ) : (
                <span className="flex items-center gap-1">
                  <span className="w-1.5 h-1.5 bg-jazari-gold rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                  <span className="w-1.5 h-1.5 bg-jazari-gold rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                  <span className="w-1.5 h-1.5 bg-jazari-gold rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                </span>
              )}
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <form onSubmit={handleSubmit} className="flex gap-2 p-2 bg-jazari-surface-light rounded-b-lg">
        {onPhotoCapture && (
          <>
            <input
              type="file"
              accept="image/*"
              capture="environment"
              className="hidden"
              ref={fileRef}
              onChange={(e) => {
                const file = e.target.files?.[0]
                if (!file) return
                const reader = new FileReader()
                reader.onload = () => {
                  const base64 = (reader.result as string).split(',')[1]
                  onPhotoCapture(base64)
                }
                reader.readAsDataURL(file)
                e.target.value = ''
              }}
            />
            <button
              type="button"
              onClick={() => fileRef.current?.click()}
              className="px-2 py-2 text-jazari-text-dim hover:text-jazari-gold transition-colors"
              aria-label="Upload photo"
            >
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-5 h-5">
                <path d="M12 9a3.75 3.75 0 100 7.5A3.75 3.75 0 0012 9z" />
                <path fillRule="evenodd" d="M9.344 3.071a49.52 49.52 0 015.312 0c.967.052 1.83.585 2.332 1.39l.821 1.317c.24.383.645.643 1.11.71.386.054.77.113 1.152.177 1.432.239 2.429 1.493 2.429 2.909V18a3 3 0 01-3 3H4.5a3 3 0 01-3-3V9.574c0-1.416.997-2.67 2.429-2.909.382-.064.766-.123 1.152-.177a1.56 1.56 0 001.11-.71l.822-1.315a2.942 2.942 0 012.332-1.39zM12 12.75a2.25 2.25 0 100 4.5 2.25 2.25 0 000-4.5z" clipRule="evenodd" />
              </svg>
            </button>
          </>
        )}
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
