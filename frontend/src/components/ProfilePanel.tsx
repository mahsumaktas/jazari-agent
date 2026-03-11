interface Props {
  profile: {
    name?: string
    active_goals?: number
    habits?: { name: string; streak: number }[]
  } | null
}

export function ProfilePanel({ profile }: Props) {
  if (!profile) return null

  return (
    <div className="bg-jazari-surface rounded-lg p-4 space-y-3">
      <h3 className="text-jazari-gold font-semibold text-sm uppercase tracking-wider">Profile</h3>
      {profile.name && (
        <p className="text-jazari-text">{profile.name}</p>
      )}
      {profile.active_goals !== undefined && (
        <p className="text-jazari-text-dim text-sm">
          {profile.active_goals} active goals
        </p>
      )}
      {profile.habits && profile.habits.length > 0 && (
        <div className="space-y-1">
          {profile.habits.map((h, i) => (
            <div key={i} className="flex justify-between text-sm">
              <span className="text-jazari-text-dim">{h.name}</span>
              <span className="text-jazari-gold">{h.streak}d streak</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
