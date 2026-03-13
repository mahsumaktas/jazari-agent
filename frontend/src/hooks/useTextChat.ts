import { useRef, useState, useCallback, useEffect } from 'react'

export type ChatMessage = {
  role: 'user' | 'assistant'
  content: string
}

export function useTextChat(userId: string) {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)
  const [isConnected, setIsConnected] = useState(false)

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const ws = new WebSocket(`${protocol}//${window.location.host}/ws?userId=${userId}`)
    wsRef.current = ws

    ws.onopen = () => setIsConnected(true)

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data)
        if (msg.type === 'text' && msg.content) {
          setMessages(prev => [...prev, { role: 'assistant', content: msg.content }])
          setIsLoading(false)
        } else if (msg.type === 'media_stored') {
          setMessages(prev => [...prev, { role: 'assistant', content: msg.content }])
        }
      } catch { /* ignore */ }
    }

    ws.onclose = () => {
      setIsConnected(false)
      setIsLoading(false)
    }

    ws.onerror = () => ws.close()
  }, [userId])

  const sendMessage = useCallback((text: string) => {
    if (!text.trim()) return
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      connect()
      setTimeout(() => sendMessage(text), 500)
      return
    }

    setMessages(prev => [...prev, { role: 'user', content: text }])
    setIsLoading(true)
    wsRef.current.send(JSON.stringify({ type: 'text', content: text }))
  }, [connect])

  useEffect(() => () => {
    wsRef.current?.close()
  }, [])

  return { messages, isLoading, isConnected, connect, sendMessage }
}
