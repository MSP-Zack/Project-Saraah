import React from 'react'
import VRMViewer from '../VRMViewer'

type Props = {
  modelUrl?: string
}

export default function PetVRM({ modelUrl = '/static/models/sarah.vrm' }: Props) {
  // Thin wrapper around existing VRMViewer. In future, this component will
  // handle root motion, animation blending, and playback of emotion clips.
  return (
    <div style={{ width: '100%', height: 520, background: 'var(--muted)' }}>
      <VRMViewer modelUrl={modelUrl} />
    </div>
  )
}
