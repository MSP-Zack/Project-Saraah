import { useState, useEffect } from 'react';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { onWebSocketMessage } from '@/hooks/useWebSocket';
import { Trash2, PlusCircle } from 'lucide-react';

interface NoteItem {
  id: string;
  title: string;
  content: string;
  pinned?: boolean;
  created_at?: string;
}

export default function NotesPanel() {
  const [notes, setNotes] = useState<NoteItem[]>([]);
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [pinned, setPinned] = useState(false);

  useEffect(() => {
    fetchNotes();

    const off = onWebSocketMessage((msg: any) => {
      if (msg.action === 'note_created' && msg.note) {
        // Show browser notification when allowed
        try {
          if (typeof Notification !== 'undefined' && Notification.permission === 'granted') {
            new Notification(msg.note.title || 'Sticky Note', { body: msg.note.content || '' });
          }
        } catch (e) {}

        setNotes((s) => [msg.note, ...s]);
      }
    });

    return () => off();
  }, []);

  const fetchNotes = async () => {
    try {
      const res = await fetch('/api/notes');
      const data = await res.json();
      setNotes(data.notes || []);
    } catch (e) { console.error('Failed to fetch notes', e); }
  };

  const createNote = async () => {
    if (!title.trim() && !content.trim()) return;
    try {
      const res = await fetch('/api/notes', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: title.trim() || 'Note', content: content.trim(), pinned })
      });
      const data = await res.json();
      if (data.success) {
        setNotes((s) => [data.note, ...s]);
        setTitle(''); setContent(''); setPinned(false);
      }
    } catch (e) { console.error('Create failed', e); }
  };

  const deleteNote = async (id: string) => {
    try {
      await fetch(`/api/notes/${id}`, { method: 'DELETE' });
      setNotes((s) => s.filter((n) => n.id !== id));
    } catch (e) { console.error('Delete failed', e); }
  };

  const pinnedNotes = notes.filter(n => n.pinned);
  const normalNotes = notes.filter(n => !n.pinned);

  return (
    <ScrollArea className="h-full px-4 py-4">
      <div className="space-y-4">
        <div className="flex items-center gap-2 mb-2">
          <PlusCircle className="w-5 h-5 text-emerald-400" />
          <h2 className="text-lg font-semibold text-white">Sticky Notes</h2>
        </div>

        <Card className="bg-white/5 border-white/10 p-3">
          <div className="grid grid-cols-1 gap-2">
            <Input placeholder="Title" value={title} onChange={(e) => setTitle(e.target.value)} />
            <Textarea placeholder="Content" value={content} onChange={(e) => setContent(e.target.value)} className="min-h-[80px]" />
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <label className="text-xs text-white/60 flex items-center gap-2"><input type="checkbox" checked={pinned} onChange={(e) => setPinned(e.target.checked)} /> Pin</label>
              </div>
              <div className="flex items-center gap-2">
                <Button size="sm" onClick={createNote}>Create</Button>
              </div>
            </div>
          </div>
        </Card>

        {pinnedNotes.length > 0 && (
          <div>
            <h3 className="text-xs text-white/60 uppercase mb-2">Pinned</h3>
            <div className="grid gap-2">
              {pinnedNotes.map(n => (
                <Card key={n.id} className="bg-white/5 border-white/10 p-2 flex justify-between items-start">
                  <div>
                    <div className="text-sm text-white font-semibold">{n.title}</div>
                    <div className="text-xs text-white/60 mt-1">{n.content}</div>
                  </div>
                  <div className="flex flex-col items-end gap-2">
                    <div className="text-xs text-white/40">{new Date(n.created_at || Date.now()).toLocaleString()}</div>
                    <Button size="sm" variant="ghost" onClick={() => deleteNote(n.id)}><Trash2 className="w-4 h-4" /></Button>
                  </div>
                </Card>
              ))}
            </div>
          </div>
        )}

        <h3 className="text-xs text-white/60 uppercase">Notes</h3>
        <div className="grid gap-2">
          {normalNotes.length === 0 && <div className="text-xs text-white/40">No notes yet.</div>}
          {normalNotes.map(n => (
            <Card key={n.id} className="bg-white/5 border-white/10 p-2 flex justify-between items-start">
              <div>
                <div className="text-sm text-white font-semibold">{n.title}</div>
                <div className="text-xs text-white/60 mt-1">{n.content}</div>
              </div>
              <div className="flex flex-col items-end gap-2">
                <div className="text-xs text-white/40">{new Date(n.created_at || Date.now()).toLocaleString()}</div>
                <Button size="sm" variant="ghost" onClick={() => deleteNote(n.id)}><Trash2 className="w-4 h-4" /></Button>
              </div>
            </Card>
          ))}
        </div>
      </div>
    </ScrollArea>
  );
}
