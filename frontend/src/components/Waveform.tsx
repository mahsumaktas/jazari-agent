import { useEffect, useRef, useMemo } from 'react'

const BAR_COUNT = 20

interface Props {
  isActive: boolean
  analyserNode?: AnalyserNode | null
}

export function Waveform({ isActive, analyserNode }: Props) {
  const barsRef = useRef<(HTMLDivElement | null)[]>([])
  const rafRef = useRef<number>(0)

  const idleDelays = useMemo(
    () => Array.from({ length: BAR_COUNT }, () => Math.random() * 500),
    [],
  )

  useEffect(() => {
    if (!isActive || !analyserNode) {
      cancelAnimationFrame(rafRef.current)
      return
    }

    const bufferLength = analyserNode.frequencyBinCount
    const dataArray = new Uint8Array(bufferLength)

    const draw = () => {
      analyserNode.getByteFrequencyData(dataArray)

      const step = Math.max(1, Math.floor(bufferLength / BAR_COUNT))

      for (let i = 0; i < BAR_COUNT; i++) {
        const bar = barsRef.current[i]
        if (!bar) continue

        const value = dataArray[Math.min(i * step, bufferLength - 1)]
        const normalized = value / 255
        const height = 4 + normalized * 40
        const opacity = 0.25 + normalized * 0.75

        bar.style.height = `${height}px`
        bar.style.opacity = `${opacity}`
      }

      rafRef.current = requestAnimationFrame(draw)
    }

    rafRef.current = requestAnimationFrame(draw)

    return () => cancelAnimationFrame(rafRef.current)
  }, [isActive, analyserNode])

  return (
    <div className="flex items-center justify-center gap-1 h-12 my-4">
      {Array.from({ length: BAR_COUNT }, (_, i) => (
        <div
          key={i}
          ref={(el) => { barsRef.current[i] = el }}
          className="w-1 rounded-full bg-jazari-gold"
          style={{
            height: '4px',
            opacity: 0.2,
            transition: (!isActive || !analyserNode)
              ? 'height 0.3s ease, opacity 0.3s ease'
              : 'none',
            animation: (isActive && !analyserNode)
              ? `waveform-idle 1.2s ease-in-out ${idleDelays[i]}ms infinite alternate`
              : 'none',
          }}
        />
      ))}
      <style>{`
        @keyframes waveform-idle {
          from { height: 4px; opacity: 0.2; }
          to { height: 14px; opacity: 0.5; }
        }
      `}</style>
    </div>
  )
}
