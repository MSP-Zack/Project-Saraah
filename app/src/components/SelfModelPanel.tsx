import { useEffect, useState } from 'react';
import { Save, UserRound } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Textarea } from '@/components/ui/textarea';

interface SelfModel {
  revision: number;
  updated_at: string | null;
  sections: Record<string, string>;
}

export default function SelfModelPanel() {
  const [model, setModel] = useState<SelfModel | null>(null);
  const [drafts, setDrafts] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState<string | null>(null);
  const [notice, setNotice] = useState('');

  const loadModel = async () => {
    try {
      const response = await fetch('/api/self-model');
      const data = await response.json() as SelfModel;
      setModel(data);
      setDrafts(data.sections || {});
    } catch {
      setNotice('Unable to load self-model.');
    }
  };

  useEffect(() => { loadModel(); }, []);

  const saveSection = async (section: string) => {
    if (!model) return;
    setSaving(section);
    setNotice('');
    try {
      const response = await fetch('/api/self-model', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ section, content: drafts[section] || '', expected_revision: model.revision }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Save failed');
      setModel(data.model);
      setDrafts(data.model.sections);
      setNotice('Self-model updated.');
    } catch (error) {
      setNotice(error instanceof Error ? error.message : 'Save failed');
      await loadModel();
    } finally {
      setSaving(null);
    }
  };

  return (
    <ScrollArea className="h-full px-4 py-4">
      <div className="space-y-4">
        <div className="flex items-center gap-2">
          <UserRound className="h-5 w-5 text-cyan-300" />
          <div>
            <h2 className="text-lg font-semibold text-white">Sarah's Self-Model</h2>
            <p className="text-[10px] text-white/40">Versioned continuity state</p>
          </div>
        </div>
        <p className="text-xs leading-relaxed text-white/50">This is Sarah's durable sense of identity, values, boundaries, relationships, and direction. Every edit creates a recoverable revision.</p>
        {notice && <p className="rounded-lg border border-cyan-400/20 bg-cyan-400/5 p-2 text-xs text-cyan-200">{notice}</p>}
        {model && Object.entries(drafts).map(([section, content]) => (
          <Card key={section} className="border-white/10 bg-white/5 p-3">
            <div className="mb-2 flex items-center justify-between">
              <label htmlFor={`self-${section}`} className="text-xs font-semibold uppercase tracking-wider text-white/65">{section.replaceAll('_', ' ')}</label>
              <Button onClick={() => saveSection(section)} disabled={saving === section} size="sm" className="h-7 gap-1 bg-cyan-500/15 text-cyan-200 hover:bg-cyan-500/25">
                <Save className="h-3 w-3" /> {saving === section ? 'Saving' : 'Save'}
              </Button>
            </div>
            <Textarea id={`self-${section}`} value={content} onChange={(event) => setDrafts((current) => ({ ...current, [section]: event.target.value }))} className="min-h-20 resize-y border-white/10 bg-black/20 text-sm text-white" />
          </Card>
        ))}
        {model && <p className="text-[10px] text-white/30">Revision {model.revision}{model.updated_at ? ` · Updated ${new Date(model.updated_at).toLocaleString()}` : ''}</p>}
      </div>
    </ScrollArea>
  );
}
