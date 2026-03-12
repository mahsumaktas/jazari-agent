import { useRef, useState, useCallback, useEffect } from 'react'

type Message = { type: string; content: string }

export function useWebSocket(userId: string) {
  const [isConnected, setIsConnected] = useState(false)
  const [transcripts, setTranscripts] = useState<Message[]>([])
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

  return { isConnected, transcripts, connect, disconnect, sendAudio, setTranscripts }
}
