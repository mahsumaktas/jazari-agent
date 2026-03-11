import { useRef, useState, useCallback, useEffect } from 'react'

type Message = { type: string; content: string }

export function useWebSocket(userId: string) {
  const [isConnected, setIsConnected] = useState(false)
  const [transcripts, setTranscripts] = useState<Message[]>([])
  const wsRef = useRef<WebSocket | null>(null)
  const audioCtxRef = useRef<AudioContext | null>(null)
  const reconnectAttempts = useRef(0)
  const MAX_RECONNECT = 3

  const connect = useCallback(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const ws = new WebSocket(`${protocol}//${window.location.host}/ws/audio?userId=${userId}`)
    ws.binaryType = 'arraybuffer'
    wsRef.current = ws

    ws.onopen = () => {
      setIsConnected(true)
      reconnectAttempts.current = 0
    }

    ws.onmessage = (event) => {
      if (event.data instanceof ArrayBuffer) {
        playAudio(event.data)
      } else {
        try {
          const msg = JSON.parse(event.data)
          if (msg.type === 'transcript') {
            setTranscripts(prev => [...prev, msg])
          }
        } catch { /* ignore non-JSON */ }
      }
    }

    ws.onclose = () => {
      setIsConnected(false)
      if (reconnectAttempts.current < MAX_RECONNECT) {
        reconnectAttempts.current++
        const delay = Math.pow(2, reconnectAttempts.current) * 1000
        setTimeout(connect, delay)
      }
    }

    ws.onerror = () => ws.close()
  }, [userId])

  const sendAudio = useCallback((data: ArrayBuffer) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(data)
    }
  }, [])

  const disconnect = useCallback(() => {
    reconnectAttempts.current = MAX_RECONNECT
    wsRef.current?.close()
  }, [])

  async function playAudio(pcmData: ArrayBuffer) {
    if (!audioCtxRef.current) {
      audioCtxRef.current = new AudioContext({ sampleRate: 24000 })
    }
    const ctx = audioCtxRef.current
    const int16 = new Int16Array(pcmData)
    const float32 = new Float32Array(int16.length)
    for (let i = 0; i < int16.length; i++) {
      float32[i] = int16[i] / 32768
    }
    const buffer = ctx.createBuffer(1, float32.length, 24000)
    buffer.copyToChannel(float32, 0)
    const source = ctx.createBufferSource()
    source.buffer = buffer
    source.connect(ctx.destination)
    source.start()
  }

  useEffect(() => () => { wsRef.current?.close() }, [])

  return { isConnected, transcripts, connect, disconnect, sendAudio, setTranscripts }
}
