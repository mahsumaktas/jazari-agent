import { useMemo } from 'react'

interface Props {
  isActive: boolean
}

export function Waveform({ isActive }: Props) {
  const bars = useMemo(() =>
    Array.from({ length: 20 }, () => ({
      baseHeight: Math.random() * 24 + 8,
      delay: Math.random() * 500,
    })), []
  )

  return (
    <div className="flex items-center justify-center gap-1 h-12 my-4">
      {bars.map((bar, i) => (
        <div
          key={i}
          className="w-1 rounded-full bg-jazari-gold transition-all duration-300"
          style={{
            height: isActive ? `${bar.baseHeight}px` : '4px',
            opacity: isActive ? 0.6 + (bar.baseHeight / 64) : 0.2,
            animation: isActive ? `pulse 0.8s ease-in-out ${bar.delay}ms infinite alternate` : 'none',
          }}
        />
      ))}
      <style>{`
        @keyframes pulse {
          from { transform: scaleY(0.6); }
          to { transform: scaleY(1.4); }
        }
      `}</style>
    </div>
  )
}
