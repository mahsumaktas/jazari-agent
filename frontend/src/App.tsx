import { useState, useCallback } from 'react'
import { MicButton } from './components/MicButton'
import { CameraButton } from './components/CameraButton'
import { Waveform } from './components/Waveform'
import { Transcript } from './components/Transcript'
import { ProfilePanel } from './components/ProfilePanel'
import { Dashboard } from './components/Dashboard'
import { useAudio } from './hooks/useAudio'
import { useWebSocket } from './hooks/useWebSocket'

function App() {
  const [userId] = useState(() => {
    let id = localStorage.getItem('jazari-user-id')
    if (!id) {
      id = crypto.randomUUID()
      localStorage.setItem('jazari-user-id', id)
    }
    return id
  })

  const { isRecording, start: startAudio, stop: stopAudio } = useAudio()
  const { isConnected, transcripts, connect, disconnect, sendAudio } = useWebSocket(userId)
  const [profile] = useState(null)
  const [todayDone] = useState<string[]>([])
  const [todayMissed] = useState<string[]>([])
  const [mediaPreview, setMediaPreview] = useState<string | null>(null)

  const handleToggle = useCallback(async () => {
    if (isRecording) {
      stopAudio()
      disconnect()
    } else {
      connect()
      await startAudio(sendAudio)
    }
  }, [isRecording, startAudio, stopAudio, connect, disconnect, sendAudio])

  const handlePhotoCapture = useCallback(async (base64: string) => {
    setMediaPreview(`data:image/jpeg;base64,${base64}`)
    const protocol = window.location.protocol === 'https:' ? 'https:' : 'http:'
    try {
      await fetch(`${protocol}//${window.location.host}/api/media-memory`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId,
          modality: 'image',
          data: base64,
          description: '',
        }),
      })
    } finally {
      setMediaPreview(null)
    }
  }, [userId])

  const handleVoiceNote = useCallback(async (base64: string) => {
    const protocol = window.location.protocol === 'https:' ? 'https:' : 'http:'
    await fetch(`${protocol}//${window.location.host}/api/media-memory`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: userId,
        modality: 'audio',
        data: base64,
        description: '',
      }),
    })
  }, [userId])

  return (
    <div className="min-h-screen bg-jazari-dark flex">
      {/* Left panel */}
      <aside className="w-64 p-4 hidden md:block">
        <ProfilePanel profile={profile} />
      </aside>

      {/* Center */}
      <main className="flex-1 flex flex-col items-center justify-center gap-6 p-8">
        <h1 className="text-3xl font-bold text-jazari-gold tracking-widest">JAZARI</h1>
        <p className="text-jazari-text-dim text-sm tracking-wide">Your AI Life Coach</p>

        <Waveform isActive={isRecording} />

        <div className="flex items-center gap-4">
          <CameraButton onCapture={handlePhotoCapture} />
          <MicButton
            isConnected={isConnected}
            isRecording={isRecording}
            onToggle={handleToggle}
            onVoiceNote={handleVoiceNote}
          />
        </div>

        <p className="text-jazari-text-dim text-xs mt-2">
          {isRecording ? 'Listening... click to stop' : 'Click to talk | Long-press for voice note'}
        </p>

        {mediaPreview && (
          <div className="w-full max-w-lg mt-4 flex justify-center">
            <div className="relative">
              <img src={mediaPreview} alt="Preview" className="w-48 h-48 object-cover rounded-lg border border-jazari-gold/30" />
              <div className="absolute bottom-2 left-2 right-2 bg-black/60 text-jazari-gold text-xs px-2 py-1 rounded">
                Storing memory...
              </div>
            </div>
          </div>
        )}

        <div className="w-full max-w-lg mt-8">
          <Transcript messages={transcripts} />
        </div>
      </main>

      {/* Right panel */}
      <aside className="w-64 p-4 hidden md:block">
        <Dashboard done={todayDone} missed={todayMissed} />
      </aside>
    </div>
  )
}

export default App
