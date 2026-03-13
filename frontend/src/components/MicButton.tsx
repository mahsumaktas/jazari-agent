import { useRef, useCallback, useState } from 'react'

interface Props {
  isConnected: boolean
  isRecording: boolean
  onToggle: () => void
  onVoiceNote?: (base64: string) => void
}

export function MicButton({ isConnected, isRecording, onToggle, onVoiceNote }: Props) {
  const pressTimer = useRef<ReturnType<typeof setTimeout> | null>(null)
  const isLongPress = useRef(false)
  const mediaRecorder = useRef<MediaRecorder | null>(null)
  const [isVoiceNoting, setIsVoiceNoting] = useState(false)

  const startVoiceNote = useCallback(async () => {
    if (!onVoiceNote) return
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
    const recorder = new MediaRecorder(stream, { mimeType: 'audio/webm' })
    const chunks: Blob[] = []

    recorder.ondataavailable = (e) => chunks.push(e.data)
    recorder.onstop = async () => {
      stream.getTracks().forEach(t => t.stop())
      const blob = new Blob(chunks, { type: 'audio/webm' })
      const reader = new FileReader()
      reader.onload = () => {
        const base64 = (reader.result as string).split(',')[1]
        onVoiceNote(base64)
      }
      reader.readAsDataURL(blob)
    }

    recorder.start()
    mediaRecorder.current = recorder
  }, [onVoiceNote])

  const handlePointerDown = useCallback(() => {
    isLongPress.current = false
    pressTimer.current = setTimeout(() => {
      isLongPress.current = true
      setIsVoiceNoting(true)
      startVoiceNote()
    }, 600)
  }, [startVoiceNote])

  const handlePointerUp = useCallback(() => {
    if (pressTimer.current) clearTimeout(pressTimer.current)
    if (isLongPress.current && mediaRecorder.current) {
      mediaRecorder.current.stop()
      mediaRecorder.current = null
      isLongPress.current = false
      setIsVoiceNoting(false)
    } else {
      onToggle()
    }
  }, [onToggle])

  return (
    <div className="flex flex-col items-center gap-2">
      <button
        onPointerDown={handlePointerDown}
        onPointerUp={handlePointerUp}
        onPointerLeave={() => {
          if (pressTimer.current) clearTimeout(pressTimer.current)
          if (mediaRecorder.current) { mediaRecorder.current.stop(); mediaRecorder.current = null; setIsVoiceNoting(false) }
        }}
        role="button"
        aria-label={isVoiceNoting ? 'Recording voice note' : isRecording ? 'Stop recording' : 'Start recording'}
        className={`w-24 h-24 rounded-full flex items-center justify-center transition-all duration-300 cursor-pointer select-none ${
          isVoiceNoting
            ? 'bg-orange-500 shadow-[0_0_40px_rgba(249,115,22,0.5)] scale-110 ring-4 ring-orange-400/50'
            : isRecording
            ? 'bg-red-600 shadow-[0_0_40px_rgba(220,38,38,0.5)] scale-110'
            : isConnected
            ? 'bg-jazari-gold hover:bg-jazari-gold-light shadow-[0_0_20px_rgba(197,165,90,0.3)]'
            : 'bg-jazari-surface-light hover:bg-jazari-gold/20'
        }`}
        style={
          isVoiceNoting
            ? { animation: 'recordingPulse 1.5s ease-in-out infinite' }
            : isRecording
            ? { animation: 'recordingPulse 1.5s ease-in-out infinite' }
            : undefined
        }
      >
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-10 h-10 text-jazari-dark">
          {isRecording ? (
            <rect x="6" y="6" width="12" height="12" rx="2" />
          ) : (
            <path d="M12 1a4 4 0 0 0-4 4v7a4 4 0 0 0 8 0V5a4 4 0 0 0-4-4zm7 11a7 7 0 0 1-14 0H3a9 9 0 0 0 8 8.94V23h2v-2.06A9 9 0 0 0 21 12h-2z" />
          )}
        </svg>
      </button>
      {isVoiceNoting && (
        <span className="text-orange-400 text-xs animate-pulse">Recording voice note...</span>
      )}
    </div>
  )
}
