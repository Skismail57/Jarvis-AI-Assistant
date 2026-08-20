import React, { useMemo } from 'react'

const WaveformAnimation = ({ active = false, bars = 32, height = 60, glow = true, className = '' }) => {
  const barCount = bars
  const delays = useMemo(
    () => Array.from({ length: barCount }, (_, i) => (i * 0.04) % 1.2),
    [barCount]
  )

  return (
    <div
      className={`flex items-end justify-center gap-[3px] ${className}`}
      style={{ height: `${height}px` }}
    >
      {Array.from({ length: barCount }).map((_, i) => {
        const staticHeight = 40 + ((i * 7) % 50)
        return (
          <div
            key={i}
            className="w-1.5 rounded-t-full rounded-b-full"
            style={{
              background: 'linear-gradient(180deg, #00eaff 0%, #7b2ff7 50%, #ff2e88 100%)',
              animation: active ? `waveform-bar 1.2s ease-in-out infinite` : 'none',
              animationDelay: active ? `${delays[i]}s` : '0s',
              height: active ? undefined : `${staticHeight}%`,
              boxShadow: glow
                ? '0 0 8px rgba(123, 47, 247, 0.6), 0 0 16px rgba(0, 234, 255, 0.3)'
                : 'none',
              transition: 'height 0.2s ease',
              minHeight: '15%',
            }}
          />
        )
      })}
    </div>
  )
}

export default WaveformAnimation
