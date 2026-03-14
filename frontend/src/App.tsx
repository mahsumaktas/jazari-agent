import { useState, useCallback, useEffect } from 'react'
import { MicButton } from './components/MicButton'
import { CameraButton } from './components/CameraButton'
import { Waveform } from './components/Waveform'
import { Transcript } from './components/Transcript'
import { TextChat } from './components/TextChat'
import { ProfilePanel } from './components/ProfilePanel'
import { Dashboard } from './components/Dashboard'
import { useAudio } from './hooks/useAudio'
import { useWebSocket } from './hooks/useWebSocket'
import { useTextChat } from './hooks/useTextChat'

function App() {
  const [userId] = useState(() => {
    let id = localStorage.getItem('jazari-user-id')
    if (!id) {
      id = crypto.randomUUID()
      localStorage.setItem('jazari-user-id', id)
    }
    return id
  })

  const { isRecording, analyserNode, start: startAudio, stop: stopAudio } = useAudio()
  const { isConnected, transcripts, partialUser, partialJazari, connect, disconnect, sendAudio } = useWebSocket(userId)
  const textChat = useTextChat(userId)
  const [mode, setMode] = useState<'voice' | 'text'>('voice')
  const [profile, setProfile] = useState(null)
  const [todayDone, setTodayDone] = useState<string[]>([])
  const [todayMissed, setTodayMissed] = useState<string[]>([])
  const [goals, setGoals] = useState<string[]>([])
  const [mediaPreview, setMediaPreview] = useState<string | null>(null)
  const [mediaStatus, setMediaStatus] = useState<'idle' | 'storing' | 'stored'>('idle')

  useEffect(() => {
    const base = `${window.location.protocol}//${window.location.host}`
    const fetchProfile = () => {
      fetch(`${base}/api/profile/${userId}`).then(r => r.json()).then(setProfile).catch(() => {})
      fetch(`${base}/api/habits/${userId}`).then(r => r.json()).then(data => {
        setTodayDone(data.done || [])
        setTodayMissed(data.missed || [])
        setGoals(data.goals || [])
      }).catch(() => {})
    }
    fetchProfile()
    const interval = setInterval(fetchProfile, 15000)
    return () => clearInterval(interval)
  }, [userId])

  useEffect(() => {
    if (mode === 'text' && !textChat.isConnected) {
      textChat.connect()
    }
  }, [mode, textChat])

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
    setMediaStatus('storing')
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
      setMediaStatus('stored')
      setTimeout(() => {
        setMediaPreview(null)
        setMediaStatus('idle')
      }, 1500)
    } catch {
      setMediaPreview(null)
      setMediaStatus('idle')
    }
  }, [userId])

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Space to toggle mic in voice mode (only when not typing in an input)
      if (e.code === 'Space' && mode === 'voice' &&
          !(e.target instanceof HTMLInputElement) &&
          !(e.target instanceof HTMLTextAreaElement)) {
        e.preventDefault()
        handleToggle()
      }
      // Escape to stop recording
      if (e.code === 'Escape' && isRecording) {
        stopAudio()
        disconnect()
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [mode, isRecording, handleToggle, stopAudio, disconnect])

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
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2 focus:bg-jazari-gold focus:text-jazari-dark focus:rounded-lg"
      >
        Skip to content
      </a>

      {/* Left panel */}
      <aside className="w-64 p-4 hidden md:block">
        <ProfilePanel profile={profile} />
      </aside>

      {/* Center */}
      <main id="main-content" className="flex-1 flex flex-col items-center justify-center gap-6 p-8">
        {/* Connection status indicator */}
        <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-jazari-surface text-xs">
          <span className={`w-2 h-2 rounded-full ${
            (mode === 'voice' ? isConnected : textChat.isConnected)
              ? 'bg-green-500'
              : 'bg-red-500'
          }`} />
          <span className="text-jazari-text-dim">
            {(mode === 'voice' ? isConnected : textChat.isConnected) ? 'Connected' : 'Disconnected'}
          </span>
          {mode === 'text' && !textChat.isConnected && (
            <button
              onClick={() => textChat.connect()}
              className="text-jazari-gold hover:text-jazari-gold-light ml-1 underline"
            >
              Retry
            </button>
          )}
        </div>

        <h1
          className="text-3xl font-bold text-jazari-gold tracking-widest"
          style={{ animation: 'fadeInUp 0.6s ease forwards', opacity: 0 }}
        >JAZARI</h1>
        <p
          className="text-jazari-text-dim text-sm tracking-wide"
          style={{ animation: 'fadeInUp 0.6s ease forwards', animationDelay: '0.2s', opacity: 0 }}
        >Your AI Life Coach</p>

        {/* Mode toggle */}
        <div
          className="flex items-center gap-1 bg-jazari-surface rounded-full p-1"
          style={{ animation: 'fadeInUp 0.6s ease forwards', animationDelay: '0.4s', opacity: 0 }}
        >
          <button
            onClick={() => setMode('voice')}
            className={`px-4 py-1.5 rounded-full text-xs font-medium transition-colors ${
              mode === 'voice' ? 'bg-jazari-gold text-jazari-dark' : 'text-jazari-text-dim hover:text-jazari-text'
            }`}
          >
            Voice
          </button>
          <button
            onClick={() => setMode('text')}
            className={`px-4 py-1.5 rounded-full text-xs font-medium transition-colors ${
              mode === 'text' ? 'bg-jazari-gold text-jazari-dark' : 'text-jazari-text-dim hover:text-jazari-text'
            }`}
          >
            Text
          </button>
        </div>

        {mode === 'voice' ? (
          <>
            <Waveform isActive={isRecording} analyserNode={analyserNode} />

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
              {isRecording ? 'Listening... click to stop' : 'Click or press Space to talk | Long-press for voice note'}
            </p>

            {mediaPreview && (
              <div className="w-full max-w-lg mt-4 flex justify-center">
                <div className="relative">
                  <img src={mediaPreview} alt="Preview" className="w-48 h-48 object-cover rounded-lg border border-jazari-gold/30" />
                  <div className={`absolute bottom-2 left-2 right-2 text-xs px-2 py-1 rounded ${
                    mediaStatus === 'stored'
                      ? 'bg-green-900/70 text-green-300'
                      : 'bg-black/60 text-jazari-gold'
                  }`}>
                    {mediaStatus === 'stored' ? 'Memory stored!' : 'Storing memory...'}
                  </div>
                </div>
              </div>
            )}

            <div className="w-full max-w-lg mt-8">
              <Transcript messages={transcripts} partialUser={partialUser} partialJazari={partialJazari} />
            </div>
          </>
        ) : (
          <div className="w-full max-w-lg mt-4">
            <TextChat
              messages={textChat.messages}
              isLoading={textChat.isLoading}
              loadingStatus={textChat.loadingStatus}
              onSend={textChat.sendMessage}
              onPhotoCapture={handlePhotoCapture}
            />
          </div>
        )}

        <div className="mt-auto pt-4">
          <p className="text-jazari-text-dim/30 text-[10px] text-center">
            {mode === 'voice' ? 'Space: Talk | Esc: Stop' : 'Enter: Send'}
          </p>
        </div>
      </main>

      {/* Right panel */}
      <aside className="w-64 p-4 hidden md:block">
        <Dashboard done={todayDone} missed={todayMissed} goals={goals} userId={userId} />
      </aside>
    </div>
  )
}

export default App
