import { useEffect, useState } from 'react';
import { Camera, Clock3, Eye, Loader2, RefreshCw } from 'lucide-react';
import { useStore } from '@/hooks/useStore';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';

async function fetchVisionObservations() {
  const response = await fetch('/api/vision/observations?limit=100');
  const data = await response.json();
  return data.observations || [];
}

export default function PerceptionPanel() {
  const store = useStore();
  const [capturing, setCapturing] = useState(false);
  const [error, setError] = useState('');

  const loadObservations = async () => {
    try {
      store.setVisionObservations(await fetchVisionObservations());
    } catch (error) {
      console.error('Failed to load visual memory:', error);
    }
  };

  const observeNow = async () => {
    setCapturing(true);
    setError('');
    try {
      const response = await fetch('/api/vision/observe', { method: 'POST' });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Could not capture a webcam observation.');
      const observation = data.observation;
      if (observation) {
        store.setWebcamVisionDescription(observation.description);
        store.setWebcamVisionTimestamp(observation.timestamp);
      }
      await loadObservations();
    } catch (captureError) {
      setError(captureError instanceof Error ? captureError.message : 'Could not capture a webcam observation.');
    } finally {
      setCapturing(false);
    }
  };

  useEffect(() => {
    fetchVisionObservations()
      .then((observations) => useStore.getState().setVisionObservations(observations))
      .catch((error) => console.error('Failed to load visual memory:', error));
  }, []);

  return (
    <ScrollArea className="h-full px-4 py-4">
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Camera className="h-5 w-5 text-violet-300" />
            <div>
              <h2 className="text-lg font-semibold text-white">Perception</h2>
              <p className="text-[10px] text-white/40">Sarah's recent visual context</p>
            </div>
          </div>
          <div className="flex items-center gap-1">
            <Button onClick={loadObservations} size="icon" variant="ghost" className="h-8 w-8 text-white/50 hover:text-white" title="Refresh observation history">
              <RefreshCw className="h-4 w-4" />
            </Button>
          </div>
        </div>

        <Button
          onClick={observeNow}
          disabled={capturing || !store.permissions.webcam_vision?.enabled}
          className="w-full gap-2 bg-blue-600 text-white hover:bg-blue-500 disabled:bg-slate-700"
          title={store.permissions.webcam_vision?.enabled ? 'Capture one webcam observation' : 'Enable webcam vision in Permissions first'}
        >
          {capturing ? <Loader2 className="h-4 w-4 animate-spin" /> : <Eye className="h-4 w-4" />}
          {capturing ? 'Observing…' : 'Observe now'}
        </Button>
        {!store.permissions.webcam_vision?.enabled && (
          <p className="-mt-2 text-[10px] text-white/40">Enable webcam vision in Permissions to capture a scene.</p>
        )}
        {error && <p role="alert" className="rounded-lg border border-red-400/20 bg-red-500/10 p-3 text-xs text-red-200">{error}</p>}

        <div className="rounded-xl border border-violet-400/20 bg-violet-500/5 p-3">
          <div className="flex items-center justify-between gap-2">
            <span className="text-[10px] uppercase tracking-[0.18em] text-violet-300">Current scene</span>
            <Badge variant="outline" className="border-violet-400/20 text-[9px] text-violet-200">
              {store.webcamVisionEnabled ? 'Live' : 'Paused'}
            </Badge>
          </div>
          <p className="mt-2 text-sm leading-relaxed text-white/85">
            {store.webcamVisionDescription || 'Enable webcam vision to begin observing the scene.'}
          </p>
          {store.webcamVisionTimestamp && (
            <p className="mt-2 text-[10px] text-white/35">Updated {new Date(store.webcamVisionTimestamp).toLocaleString()}</p>
          )}
        </div>

        <div className="flex items-center justify-between">
          <span className="text-xs font-medium text-white/70">Observation history</span>
          <span className="text-[10px] text-white/35">{store.visionObservations.length} saved</span>
        </div>

        <div className="space-y-2">
          {[...store.visionObservations].reverse().map((observation, index) => (
            <div key={`${observation.timestamp}-${observation.id ?? index}`} className="rounded-lg border border-white/10 bg-white/5 p-3">
              <div className="mb-1 flex items-center gap-1.5 text-[10px] text-white/35">
                <Clock3 className="h-3 w-3" />
                <span>{new Date(observation.timestamp).toLocaleString()}</span>
                <span className="ml-auto uppercase tracking-wider">{observation.source}</span>
              </div>
              <p className="text-xs leading-relaxed text-white/75">{observation.description}</p>
            </div>
          ))}
          {store.visionObservations.length === 0 && (
            <p className="py-8 text-center text-sm text-white/30">No visual observations recorded yet.</p>
          )}
        </div>
      </div>
    </ScrollArea>
  );
}
