interface Props {
  done: string[]
  missed: string[]
}

export function Dashboard({ done, missed }: Props) {
  return (
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
      {done.length === 0 && missed.length === 0 && (
        <p className="text-jazari-text-dim text-sm">No habits tracked yet</p>
      )}
    </div>
  )
}
