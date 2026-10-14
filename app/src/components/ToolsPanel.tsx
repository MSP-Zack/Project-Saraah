import { useEffect, useState } from 'react';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { List } from 'lucide-react';

export default function ToolsPanel() {
  const [tools, setTools] = useState<any>(null);

  useEffect(() => {
    fetch('/api/tools').then(r => r.json()).then(setTools).catch(() => setTools(null));
  }, []);

  return (
    <ScrollArea className="h-full px-4 py-4">
      <div className="space-y-4">
        <div className="flex items-center gap-2 mb-2">
          <List className="w-5 h-5 text-cyan-400" />
          <h2 className="text-lg font-semibold text-white">Tools & Plugins</h2>
        </div>

        <Card className="bg-white/5 border-white/10 p-3">
          <div className="text-sm text-white/70 mb-2">Loaded plugins and available tools</div>
          {tools ? (
            <div className="space-y-2 text-xs text-white/60">
              <div>Plugins:</div>
              {tools.plugins && tools.plugins.length > 0 ? (
                tools.plugins.map((p: any) => (
                  <div key={p.name} className="p-2 bg-white/3 rounded-md flex items-center justify-between">
                    <div>
                      <div className="font-medium text-white">{p.name}</div>
                      <div className="text-[10px] text-white/50">{p.info?.description || ''}</div>
                    </div>
                    <div>
                      <Button size="sm" onClick={() => alert(JSON.stringify(p.info || {}, null, 2))}>Info</Button>
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-xs text-white/40">No plugins loaded</div>
              )}

              <div className="mt-3">VRM actions: {tools.vrm_actions_available ? 'yes' : 'no'}</div>
            </div>
          ) : (
            <div className="text-xs text-white/50">Loading tools...</div>
          )}
        </Card>
      </div>
    </ScrollArea>
  );
}
