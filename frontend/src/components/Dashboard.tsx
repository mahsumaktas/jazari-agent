import { useState, useEffect } from 'react'

interface Props {
  done: string[]
  missed: string[]
  goals: string[]
  userId: string
}

interface Memory {
  content: string
  memory_type: string
  created_at: string
  modality: string
}

export function Dashboard({ done, missed, goals, userId }: Props) {
  const [memories, setMemories] = useState<Memory[]>([])

  useEffect(() => {
    const base = `${window.location.protocol}//${window.location.host}`
    const fetchMemories = () => {
      fetch(`${base}/api/memories/${userId}?limit=5`)
        .then(r => r.json())
        .then(data => setMemories(data.memories || []))
        .catch(() => {})
    }
    fetchMemories()
    // Refresh every 15s to catch new memories from conversation
    const interval = setInterval(fetchMemories, 15000)
    return () => clearInterval(interval)
  }, [userId])

  const typeIcon = (type: string) => {
    switch (type) {
      case 'goal': return '🎯'
      case 'habit': return '💪'
      case 'fact': return '📝'
      case 'visual': return '📷'
      case 'audio': return '🎤'
      default: return '💡'
    }
  }

  return (
    <div className="space-y-4">
      {/* Today's Habits */}
      <div className="bg-jazari-surface rounded-lg p-4 space-y-3">
        <h3 className="text-jazari-gold font-semibold text-sm uppercase tracking-wider">Today</h3>
        {done.length > 0 && (
          <div className="space-y-1">
            {done.map((item, i) => (
              <div key={i} className="flex items-center gap-2 text-sm">
                <span className="text-green-500">&#10003;</span>
                <span className="text-jazari-text-dim">{item}</span>
              </div>
            ))}
          </div>
        )}
        {missed.length > 0 && (
          <div className="space-y-1">
            {missed.map((item, i) => (
              <div key={i} className="flex items-center gap-2 text-sm">
                <span className="text-red-500">&#10007;</span>
                <span className="text-jazari-text-dim">{item}</span>
              </div>
            ))}
          </div>
        )}
        {goals.length > 0 && (
          <div className="space-y-1">
            <p className="text-jazari-text-dim/50 text-[10px] uppercase tracking-wider mt-1">Goals</p>
            {goals.map((item, i) => (
              <div key={i} className="flex items-center gap-2 text-sm">
                <span className="text-jazari-gold">&#9670;</span>
                <span className="text-jazari-text-dim">{item}</span>
              </div>
            ))}
          </div>
        )}
        {done.length === 0 && missed.length === 0 && goals.length === 0 && (
          <p className="text-jazari-text-dim text-sm">No habits or goals yet</p>
        )}
      </div>

      {/* Memory Timeline */}
      <div className="bg-jazari-surface rounded-lg p-4 space-y-3">
        <h3 className="text-jazari-gold font-semibold text-sm uppercase tracking-wider">Memories</h3>
        {memories.length > 0 ? (
          <div className="space-y-2">
            {memories.map((mem, i) => (
              <div key={i} className="flex items-start gap-2 text-sm border-l-2 border-jazari-gold/20 pl-3 py-1">
                <span className="text-xs mt-0.5 shrink-0">{typeIcon(mem.memory_type)}</span>
                <div className="min-w-0">
                  <p className="text-jazari-text-dim truncate">{mem.content}</p>
                  <p className="text-jazari-text-dim/50 text-[10px] mt-0.5">
                    {mem.modality !== 'text' && <span className="text-jazari-gold">{mem.modality} </span>}
                    {new Date(mem.created_at).toLocaleDateString()}
                  </p>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-jazari-text-dim text-sm">No memories yet</p>
        )}
      </div>
    </div>
  )
}
