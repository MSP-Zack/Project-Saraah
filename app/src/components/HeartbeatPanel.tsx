import { useEffect, useState } from 'react';
import { Activity, Ban, Save } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { ScrollArea } from '@/components/ui/scroll-area';

interface HeartbeatState {
  enabled: boolean;
  interval_minutes: number;
  max_runs_per_day: number;
  min_idle_minutes: number;
  runs_today: number;
  running: boolean;
  current_reason: string | null;
  history: { timestamp: string; status: string; decision?: string; reason?: string; summary: string }[];
}

export default function HeartbeatPanel() {
  const [state, setState] = useState<HeartbeatState | null>(null);
  const [notice, setNotice] = useState('');

  const load = async () => {
    try {
      const response = await fetch('/api/heartbeat');
      setState(await response.json());
    } catch {
      setNotice('Unable to load heartbeat settings.');
    }
  };

  useEffect(() => { load(); }, []);

  const save = async (patch: Partial<HeartbeatState>) => {
    const response = await fetch('/api/heartbeat', {
      method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(patch),
    });
    const data = await response.json();
    if (response.ok) { setState(data.heartbeat); setNotice('Heartbeat settings saved.'); }
    else setNotice(data.detail || 'Unable to save heartbeat settings.');
  };

  const cancel = async () => {
    await fetch('/api/heartbeat/cancel', { method: 'POST' });
    await load();
    setNotice('Cancellation requested.');
  };

  if (!state) return <div className="p-4 text-sm text-white/40">Loading heartbeat...</div>;

  return (
    <ScrollArea className="h-full px-4 py-4">
      <div className="space-y-4">
        <div className="flex items-center gap-2"><Activity className="h-5 w-5 text-emerald-300" /><div><h2 className="text-lg font-semibold text-white">Heartbeat</h2><p className="text-[10px] text-white/40">Guarded autonomous reflection</p></div></div>
        <Card className="border-emerald-400/20 bg-emerald-500/5 p-3"><p className="text-xs leading-relaxed text-white/65">When enabled, Sarah may wake during genuine idle time to review her goals and continuity. Every run is capped, logged, and cancellable.</p></Card>
        <div className="flex items-center justify-between rounded-xl border border-white/10 bg-white/5 p-3"><div><Label className="text-sm text-white">Enable heartbeat</Label><p className="text-[10px] text-white/40">Off by default</p></div><Switch checked={state.enabled} onCheckedChange={(enabled) => save({ enabled })} /></div>
        <Card className="space-y-3 border-white/10 bg-white/5 p-3">
          <div><Label className="text-xs text-white/65">Interval between runs (minutes)</Label><Input type="number" min={5} max={1440} value={state.interval_minutes} onChange={(event) => setState({ ...state, interval_minutes: Number(event.target.value) })} onBlur={() => save({ interval_minutes: state.interval_minutes })} className="mt-1 border-white/10 bg-black/20 text-white" /></div>
          <div><Label className="text-xs text-white/65">Minimum user idle time (minutes)</Label><Input type="number" min={0} max={1440} value={state.min_idle_minutes} onChange={(event) => setState({ ...state, min_idle_minutes: Number(event.target.value) })} onBlur={() => save({ min_idle_minutes: state.min_idle_minutes })} className="mt-1 border-white/10 bg-black/20 text-white" /></div>
          <div><Label className="text-xs text-white/65">Maximum runs per day</Label><Input type="number" min={1} max={100} value={state.max_runs_per_day} onChange={(event) => setState({ ...state, max_runs_per_day: Number(event.target.value) })} onBlur={() => save({ max_runs_per_day: state.max_runs_per_day })} className="mt-1 border-white/10 bg-black/20 text-white" /></div>
        </Card>
        <div className="flex items-center justify-between text-xs text-white/50"><span>{state.runs_today} / {state.max_runs_per_day} runs today</span><Badge variant="outline" className={state.running ? 'border-amber-400/30 text-amber-200' : 'border-white/15 text-white/45'}>{state.running ? 'Running' : 'Idle'}</Badge></div>
        {state.current_reason && <Card className="border-amber-400/20 bg-amber-500/5 p-3"><p className="text-[10px] uppercase tracking-wider text-amber-200/70">Current wake reason</p><p className="mt-1 text-xs text-white/70">{state.current_reason}</p></Card>}
        {state.running && <Button onClick={cancel} variant="outline" className="w-full gap-2 border-rose-400/30 text-rose-200 hover:bg-rose-500/10"><Ban className="h-4 w-4" /> Request cancellation</Button>}
        {notice && <p className="text-xs text-cyan-200">{notice}</p>}
        <div className="space-y-2"><div className="flex items-center gap-2 text-xs font-medium text-white/65"><Save className="h-3 w-3" /> Activity history</div>{state.history.map((entry) => <div key={entry.timestamp} className="rounded-lg border border-white/10 bg-white/5 p-2"><div className="flex justify-between text-[10px] text-white/35"><span>{entry.status}{entry.decision ? ` · ${entry.decision}` : ''}</span><span>{new Date(entry.timestamp).toLocaleString()}</span></div>{entry.reason && <p className="mt-1 text-[10px] text-amber-200/60">Reason: {entry.reason}</p>}<p className="mt-1 text-xs text-white/60">{entry.summary}</p></div>)}</div>
      </div>
    </ScrollArea>
  );
}
