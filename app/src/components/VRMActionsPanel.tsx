import { useEffect, useState } from 'react';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Switch } from '@/components/ui/switch';
import { getWebSocket } from '@/hooks/useWebSocket';
import { Smile, Play } from 'lucide-react';

export default function VRMActionsPanel() {
  const [actions, setActions] = useState<any>(null);
  const [hidden, setHidden] = useState<boolean>(true);

  useEffect(() => {
    fetch('/api/vrm/actions').then(r => r.json()).then(setActions).catch(() => setActions(null));
    setHidden((window as any).__vrm_manual_hidden ?? true);
  }, []);

  const toggleHidden = (v: boolean) => {
    setHidden(v);
    const ws = getWebSocket();
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: 'config_update', config: { vrm_manual_hidden: v } }));
    }
    (window as any).__vrm_manual_hidden = v;
  };

  const sendAction = (name: string, params: any = {}) => {
    const ws = getWebSocket();
    if (!ws || ws.readyState !== WebSocket.OPEN) return alert('Not connected');
    ws.send(JSON.stringify({ type: 'vrm_manual_action', action: name, params }));
  };

  return (
    <ScrollArea className="h-full px-4 py-4">
      <div className="space-y-4">
        <div className="flex items-center gap-2 mb-2">
          <Smile className="w-5 h-5 text-yellow-400" />
          <h2 className="text-lg font-semibold text-white">VRM Actions</h2>
        </div>

        <Card className="bg-white/5 border-white/10 p-3">
          <div className="flex items-center justify-between">
            <div className="text-sm text-white/70">Manual VRM Control</div>
            <div className="flex items-center gap-2">
              <div className="text-xs text-white/50">Hide from LLM</div>
              <Switch checked={hidden} onCheckedChange={toggleHidden} />
            </div>
          </div>

          <div className="mt-3 text-xs text-white/60">Expressions</div>
          <div className="grid grid-cols-2 gap-2 mt-2">
            {actions?.expressions ? Object.keys(actions.expressions).map((k: string) => (
              <Button key={k} size="sm" onClick={() => sendAction(k)} className="text-xs">{k}</Button>
            )) : <div className="text-xs text-white/40">No expressions</div>}
          </div>

          <div className="mt-3 text-xs text-white/60">Animations</div>
          <div className="grid grid-cols-2 gap-2 mt-2">
            {actions?.animations ? Object.keys(actions.animations).map((k: string) => (
              <div key={k} className="flex items-center justify-between">
                <div className="text-xs text-white/60">{k}</div>
                <Button size="sm" onClick={() => sendAction(k)}><Play className="w-3 h-3" /></Button>
              </div>
            )) : <div className="text-xs text-white/40">No animations</div>}
          </div>

          <div className="mt-3 text-xs text-white/60">Body Interactions (click handlers)</div>
          <div className="grid grid-cols-2 gap-2 mt-2">
            {actions?.body_interactions ? Object.keys(actions.body_interactions).map((k: string) => (
              <Button key={k} size="sm" onClick={() => sendAction(k)} className="text-xs">{k}</Button>
            )) : <div className="text-xs text-white/40">No body interactions</div>}
          </div>
        </Card>
      </div>
    </ScrollArea>
  );
}
