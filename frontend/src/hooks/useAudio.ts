import { useRef, useState, useCallback } from 'react'

export function useAudio() {
  const [isRecording, setIsRecording] = useState(false)
  const audioContextRef = useRef<AudioContext | null>(null)
  const processorRef = useRef<ScriptProcessorNode | null>(null)
  const streamRef = useRef<MediaStream | null>(null)

  const start = useCallback(async (onAudioData: (data: ArrayBuffer) => void) => {
    const stream = await navigator.mediaDevices.getUserMedia({
      audio: { sampleRate: 16000, channelCount: 1, echoCancellation: true },
    })
    streamRef.current = stream

    const ctx = new AudioContext({ sampleRate: 16000 })
    audioContextRef.current = ctx

    const source = ctx.createMediaStreamSource(stream)
    const processor = ctx.createScriptProcessor(4096, 1, 1)
    processorRef.current = processor

    processor.onaudioprocess = (e) => {
      const float32 = e.inputBuffer.getChannelData(0)
      const int16 = new Int16Array(float32.length)
      for (let i = 0; i < float32.length; i++) {
        int16[i] = Math.max(-32768, Math.min(32767, Math.floor(float32[i] * 32768)))
      }
      onAudioData(int16.buffer)
    }

    source.connect(processor)
    processor.connect(ctx.destination)
    setIsRecording(true)
  }, [])

  const stop = useCallback(() => {
    processorRef.current?.disconnect()
    audioContextRef.current?.close()
    streamRef.current?.getTracks().forEach(t => t.stop())
    setIsRecording(false)
  }, [])

  return { isRecording, start, stop }
}
