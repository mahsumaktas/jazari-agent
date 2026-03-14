import { useRef, useState, useCallback, useEffect } from 'react'

export type TranscriptMessage = {
  content: string
  sender: 'user' | 'jazari'
  timestamp: string
}

export function useWebSocket(userId: string) {
  const [isConnected, setIsConnected] = useState(false)
  const [transcripts, setTranscripts] = useState<TranscriptMessage[]>([])
  const [partialUser, setPartialUser] = useState('')
  const [partialJazari, setPartialJazari] = useState('')
  const wsRef = useRef<WebSocket | null>(null)
  const audioCtxRef = useRef<AudioContext | null>(null)
  const workletNodeRef = useRef<AudioWorkletNode | null>(null)
  const reconnectAttempts = useRef(0)
  const MAX_RECONNECT = 3

  async function initAudioPlayback() {
    if (audioCtxRef.current) return

    // Match Gemini's output sample rate exactly
    const ctx = new AudioContext({ sampleRate: 24000 })
    await ctx.audioWorklet.addModule('/audio-processor.js')

    const workletNode = new AudioWorkletNode(ctx, 'stream-processor')
    workletNode.connect(ctx.destination)

    audioCtxRef.current = ctx
    workletNodeRef.current = workletNode
  }

  function formatTimestamp(): string {
    return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }

  const connect = useCallback(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const ws = new WebSocket(`${protocol}//${window.location.host}/ws/audio?userId=${userId}`)
    ws.binaryType = 'arraybuffer'
    wsRef.current = ws

    ws.onopen = async () => {
      setIsConnected(true)
      reconnectAttempts.current = 0
      await initAudioPlayback()
    }

    ws.onmessage = (event) => {
      if (event.data instanceof ArrayBuffer) {
        // Send Int16 PCM directly to AudioWorklet
        const int16 = new Int16Array(event.data)
        if (int16.length > 0 && workletNodeRef.current) {
          workletNodeRef.current.port.postMessage(
            { event: 'write', buffer: int16 },
            [int16.buffer]  // Transfer ownership for performance
          )
        }
      } else {
        try {
          const msg = JSON.parse(event.data)
          if (msg.type === 'transcript') {
            const sender = msg.sender === 'jazari' ? 'jazari' : 'user'
            const finished = msg.finished !== false

            if (finished) {
              // Final transcript — add to history, skip duplicates
              setTranscripts(prev => {
                const last = prev[prev.length - 1]
                if (last && last.sender === sender && last.content === msg.content) {
                  return prev // skip duplicate
                }
                return [...prev, {
                  content: msg.content,
                  sender,
                  timestamp: formatTimestamp(),
                }]
              })
              if (sender === 'user') setPartialUser('')
              else setPartialJazari('')
            } else {
              // Partial — update live preview
              if (sender === 'user') setPartialUser(msg.content)
              else setPartialJazari(msg.content)
            }
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

    // Clean up audio worklet
    if (workletNodeRef.current) {
      workletNodeRef.current.port.postMessage({ event: 'clear' })
      workletNodeRef.current.disconnect()
      workletNodeRef.current = null
    }
    if (audioCtxRef.current) {
      audioCtxRef.current.close()
      audioCtxRef.current = null
    }
  }, [])

  useEffect(() => () => {
    wsRef.current?.close()
    audioCtxRef.current?.close()
  }, [])

  return { isConnected, transcripts, partialUser, partialJazari, connect, disconnect, sendAudio, setTranscripts }
}
