import { useRef, useState, useCallback } from 'react'

const TARGET_RATE = 24000

export function useAudio() {
  const [isRecording, setIsRecording] = useState(false)
  const [analyserNode, setAnalyserNode] = useState<AnalyserNode | null>(null)
  const audioContextRef = useRef<AudioContext | null>(null)
  const processorRef = useRef<ScriptProcessorNode | null>(null)
  const streamRef = useRef<MediaStream | null>(null)

  const start = useCallback(async (onAudioData: (data: ArrayBuffer) => void) => {
    const stream = await navigator.mediaDevices.getUserMedia({
      audio: { channelCount: 1, echoCancellation: true },
    })
    streamRef.current = stream

    // Use browser's native sample rate for best quality
    const ctx = new AudioContext()
    audioContextRef.current = ctx
    const nativeRate = ctx.sampleRate

    const source = ctx.createMediaStreamSource(stream)

    const analyser = ctx.createAnalyser()
    analyser.fftSize = 64
    analyser.smoothingTimeConstant = 0.8
    source.connect(analyser)
    setAnalyserNode(analyser)

    const processor = ctx.createScriptProcessor(4096, 1, 1)
    processorRef.current = processor

    processor.onaudioprocess = (e) => {
      const inputData = e.inputBuffer.getChannelData(0)

      // Resample from native rate to 24kHz if needed
      let samples: Float32Array
      if (nativeRate === TARGET_RATE) {
        samples = inputData
      } else {
        const ratio = nativeRate / TARGET_RATE
        const newLength = Math.round(inputData.length / ratio)
        samples = new Float32Array(newLength)
        for (let i = 0; i < newLength; i++) {
          const srcIndex = i * ratio
          const low = Math.floor(srcIndex)
          const high = Math.min(low + 1, inputData.length - 1)
          const frac = srcIndex - low
          // Linear interpolation
          samples[i] = inputData[low] * (1 - frac) + inputData[high] * frac
        }
      }

      // Convert Float32 to Int16
      const int16 = new Int16Array(samples.length)
      for (let i = 0; i < samples.length; i++) {
        int16[i] = Math.max(-32768, Math.min(32767, Math.floor(samples[i] * 32768)))
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
    setAnalyserNode(null)
    setIsRecording(false)
  }, [])

  return { isRecording, analyserNode, start, stop }
}
