import { useEffect, useRef } from 'react'

interface Message {
  type: string
  content: string
}

interface Props {
  messages: Message[]
}

export function Transcript({ messages }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  return (
    <div className="max-h-48 overflow-y-auto space-y-2 p-4 bg-jazari-surface rounded-lg">
      {messages.length === 0 ? (
        <p className="text-jazari-text-dim text-sm text-center">
          Press the mic to start talking to Jazari
        </p>
      ) : (
        messages.map((msg, i) => (
          <p key={i} className={`text-sm ${
            msg.content.startsWith('[user]')
              ? 'text-jazari-text-dim'
              : 'text-jazari-text'
          }`}>
            {msg.content}
          </p>
        ))
      )}
      <div ref={bottomRef} />
    </div>
  )
}
