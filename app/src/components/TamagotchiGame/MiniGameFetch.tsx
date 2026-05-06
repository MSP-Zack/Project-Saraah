import React, { useState, useRef, useEffect } from 'react'

type SessionInfo = {
  session_id: string
  max_score: number
  rounds: number
}

export default function MiniGameFetch() {
  const [session, setSession] = useState<SessionInfo | null>(null)
  const [running, setRunning] = useState(false)
  const [score, setScore] = useState(0)
  const [currentTarget, setCurrentTarget] = useState<{ x: number; y: number } | null>(null)
  const [roundIndex, setRoundIndex] = useState(0)
  const timeoutRef = useRef<number | null>(null)

  useEffect(() => {
    return () => {
      if (timeoutRef.current) window.clearTimeout(timeoutRef.current)
    }
  }, [])

  const start = async () => {
    try {
      const res = await fetch('/api/pet/mini-game/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ game: 'fetch', difficulty: 'normal' })
      })
      const data = await res.json()
      if (data.success) {
        setSession({ session_id: data.session_id, max_score: data.max_score, rounds: data.rounds })
        setScore(0)
        setRoundIndex(0)
        setRunning(true)
        nextRound(0, data.rounds)
      } else {
        alert('Failed to start mini-game: ' + (data.error || 'unknown'))
      }
    } catch (e) {
      alert('Network error')
    }
  }

  function nextRound(i: number, total: number) {
    if (i >= total) {
      finish()
      return
    }
    setRoundIndex(i + 1)
    // spawn target at random location
    const x = 10 + Math.random() * 260
    const y = 10 + Math.random() * 180
    setCurrentTarget({ x, y })

    // target visible for 800ms
    timeoutRef.current = window.setTimeout(() => {
      setCurrentTarget(null)
      nextRound(i + 1, total)
    }, 800)
  }

  const hitTarget = () => {
    if (!currentTarget) return
    setScore((s) => s + 1)
    setCurrentTarget(null)
  }

  const finish = async () => {
    setRunning(false)
    // submit result
    try {
      const res = await fetch('/api/pet/mini-game/submit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: session?.session_id, score })
      })
      const data = await res.json()
      if (data.success) {
        alert(`Game over — score ${score}/${session?.max_score}. Rewards applied.`)
        // ask server for latest state
        fetch('/api/pet/state').then(() => {})
      } else {
        alert('Submit failed: ' + (data.error || 'unknown'))
      }
    } catch (e) {
      alert('Network error')
    }
  }

  return (
    <div style={{ padding: 12, border: '1px solid rgba(255,255,255,0.06)', borderRadius: 8 }}>
      <strong>Fetch Mini-game</strong>
      {!running && (
        <div style={{ marginTop: 8 }}>
          <button onClick={start}>Start Fetch</button>
        </div>
      )}

      {running && (
        <div style={{ marginTop: 8 }}>
          <div style={{ width: 280, height: 200, position: 'relative', background: '#071226', borderRadius: 8 }} onClick={hitTarget}>
            {currentTarget && (
              <div style={{ position: 'absolute', left: currentTarget.x, top: currentTarget.y }}>
                <div style={{ width: 24, height: 24, borderRadius: 12, background: '#ffcc00', boxShadow: '0 0 8px #ffcc00' }} />
              </div>
            )}
          </div>
          <div style={{ marginTop: 8 }}>
            Round: {roundIndex}/{session?.rounds} — Score: {score}
          </div>
        </div>
      )}
    </div>
  )
}
