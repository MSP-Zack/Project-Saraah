import React, { useState } from 'react'
import PetVRM from './PetVRM'
import HUD from './HUD'
import MiniGameFetch from './MiniGameFetch'

type PetState = {
  hunger: number
  energy: number
  happiness: number
  hygiene: number
  health: number
}

const initialState: PetState = { hunger: 80, energy: 80, happiness: 80, hygiene: 80, health: 100 }

export default function TamagotchiGame() {
  const [state, setState] = useState<PetState>(initialState)

  function handleAction(action: string) {
    // Local optimistic updates; real integration will call plugin APIs
    if (action === 'feed') {
      setState(s => ({ ...s, hunger: Math.min(100, s.hunger + 25) }))
    } else if (action === 'pet') {
      setState(s => ({ ...s, happiness: Math.min(100, s.happiness + 12) }))
    } else if (action === 'play') {
      setState(s => ({ ...s, happiness: Math.min(100, s.happiness + 20), energy: Math.max(0, s.energy - 15) }))
    } else if (action === 'clean') {
      setState(s => ({ ...s, hygiene: 100, happiness: Math.min(100, s.happiness + 5) }))
    }
    console.log('Tamagotchi action:', action)
    // Forward move events for the pet to test simple locomotion
    if (action === 'wander') {
      const evt = new CustomEvent('pet-move', { detail: { x: 1 + Math.random() * 2, y: 0, z: 0.5 + Math.random() * 1.5, speed: 1.2 } });
      window.dispatchEvent(evt);
    }
  }

  return (
    <div style={{ display: 'flex', gap: 16, alignItems: 'flex-start' }}>
      <div style={{ flex: '1 1 60%' }}>
        <PetVRM modelUrl="/static/models/sarah.vrm" />
      </div>

      <div style={{ width: 360 }}>
        <HUD state={state} />

        <div style={{ marginTop: 12, display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          <button onClick={() => handleAction('feed')}>Feed</button>
          <button onClick={() => handleAction('pet')}>Pet</button>
          <button onClick={() => handleAction('play')}>Play</button>
          <button onClick={() => handleAction('clean')}>Clean</button>
        </div>

        <div style={{ marginTop: 18 }}>
          <MiniGameFetch />
        </div>
      </div>
    </div>
  )
}
