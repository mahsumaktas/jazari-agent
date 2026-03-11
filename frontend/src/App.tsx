import { useState, useCallback } from 'react'
import { MicButton } from './components/MicButton'
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

  const handleToggle = useCallback(async () => {
    if (isRecording) {
      stopAudio()
      disconnect()
    } else {
      connect()
      await startAudio(sendAudio)
    }
  }, [isRecording, startAudio, stopAudio, connect, disconnect, sendAudio])

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
        <MicButton
          isConnected={isConnected}
          isRecording={isRecording}
          onToggle={handleToggle}
        />
        <p className="text-jazari-text-dim text-xs mt-2">
          {isRecording ? 'Listening... click to stop' : 'Click to start talking'}
        </p>

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
