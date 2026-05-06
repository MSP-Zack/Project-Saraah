import React from 'react'

type Props = {
  state: {
    hunger: number
    energy: number
    happiness: number
    hygiene: number
    health: number
  }
}

function Bar({ label, value }: { label: string; value: number }) {
  return (
    <div style={{ marginBottom: 8 }}>
      <div style={{ fontSize: 12, marginBottom: 4 }}>{label}</div>
      <div style={{ background: '#222', height: 10, borderRadius: 6 }}>
        <div style={{ width: `${value}%`, height: 10, background: '#6ee7b7', borderRadius: 6 }} />
      </div>
    </div>
  )
}

export default function HUD({ state }: Props) {
  return (
    <div style={{ padding: 12, border: '1px solid rgba(255,255,255,0.06)', borderRadius: 8 }}>
      <h3 style={{ marginTop: 0 }}>Pet Status</h3>
      <Bar label={`Hunger (${Math.round(state.hunger)})`} value={state.hunger} />
      <Bar label={`Energy (${Math.round(state.energy)})`} value={state.energy} />
      <Bar label={`Happiness (${Math.round(state.happiness)})`} value={state.happiness} />
      <Bar label={`Hygiene (${Math.round(state.hygiene)})`} value={state.hygiene} />
      <Bar label={`Health (${Math.round(state.health)})`} value={state.health} />
    </div>
  )
}
