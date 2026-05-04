import { useState, useEffect } from 'react';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Brain, Search, Trash2, Edit2, Save, X, Database, MessageSquare, Star } from 'lucide-react';

interface MemoryEntry {
  id: number;
  title: string;
  content: string;
  importance: number;
  timestamp: string;
}

interface ConversationEntry {
  id: number;
  role: string;
  content: string;
  timestamp: string;
}

export default function MemoryPanel() {
  const [memories, setMemories] = useState<MemoryEntry[]>([]);
  const [conversations, setConversations] = useState<ConversationEntry[]>([]);
  const [facts, setFacts] = useState<Record<string, any[]>>({});
  const [stats, setStats] = useState({ total_conversations: 0, total_memories: 0, total_facts: 0 });
  const [searchQuery, setSearchQuery] = useState('');
  const [activeView, setActiveView] = useState<'memories' | 'conversations' | 'facts'>('memories');
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editTitle, setEditTitle] = useState('');
  const [editContent, setEditContent] = useState('');
  const [editImportance, setEditImportance] = useState(5);

  useEffect(() => {
    fetchMemory();
  }, []);

  const fetchMemory = async () => {
    try {
      const res = await fetch('/api/memory');
      const data = await res.json();
      setMemories(data.memories || []);
      setConversations(data.conversations || []);
      setFacts(data.facts || {});
      setStats(data.stats || { total_conversations: 0, total_memories: 0, total_facts: 0 });
    } catch (e) {
      console.error('Failed to fetch memory:', e);
    }
  };

  const searchMemory = async () => {
    if (!searchQuery.trim()) {
      fetchMemory();
      return;
    }
    try {
      const res = await fetch(`/api/memory/search?query=${encodeURIComponent(searchQuery)}`);
      const data = await res.json();
      // Show search results in conversations view
      setConversations(data.results || []);
      setActiveView('conversations');
    } catch (e) {
      console.error('Search failed:', e);
    }
  };

  const deleteMemory = async (id: number) => {
    try {
      await fetch(`/api/memory/${id}`, { method: 'DELETE' });
      fetchMemory();
    } catch (e) {
      console.error('Delete failed:', e);
    }
  };

  const startEdit = (m: MemoryEntry) => {
    setEditingId(m.id);
    setEditTitle(m.title);
    setEditContent(m.content);
    setEditImportance(m.importance);
  };

  const saveEdit = async () => {
    if (editingId === null) return;
    try {
      await fetch('/api/memory/edit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          memory_id: editingId,
          title: editTitle,
          content: editContent,
          importance: editImportance,
        }),
      });
      setEditingId(null);
      fetchMemory();
    } catch (e) {
      console.error('Edit failed:', e);
    }
  };

  const formatTime = (iso: string) => {
    try { return new Date(iso).toLocaleString(); } catch { return iso; }
  };

  return (
    <ScrollArea className="h-full px-4 py-4">
      <div className="space-y-4">
        <div className="flex items-center gap-2 mb-2">
          <Brain className="w-5 h-5 text-purple-400" />
          <h2 className="text-lg font-semibold text-white">Memory</h2>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-3 gap-2">
          <Card className="bg-white/5 border-white/10 p-2 text-center">
            <MessageSquare className="w-4 h-4 text-cyan-400 mx-auto mb-1" />
            <p className="text-lg font-bold text-white">{stats.total_conversations}</p>
            <p className="text-[9px] text-white/40">Chats</p>
          </Card>
          <Card className="bg-white/5 border-white/10 p-2 text-center">
            <Star className="w-4 h-4 text-yellow-400 mx-auto mb-1" />
            <p className="text-lg font-bold text-white">{stats.total_memories}</p>
            <p className="text-[9px] text-white/40">Memories</p>
          </Card>
          <Card className="bg-white/5 border-white/10 p-2 text-center">
            <Database className="w-4 h-4 text-emerald-400 mx-auto mb-1" />
            <p className="text-lg font-bold text-white">{stats.total_facts}</p>
            <p className="text-[9px] text-white/40">Facts</p>
          </Card>
        </div>

        {/* Search */}
        <div className="flex gap-2">
          <Input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search memory..."
            className="bg-white/5 border-white/10 text-white placeholder:text-white/30 h-8 text-sm"
            onKeyDown={(e) => e.key === 'Enter' && searchMemory()}
          />
          <Button onClick={searchMemory} size="sm" variant="ghost" className="h-8 px-2 text-white/60 hover:text-white">
            <Search className="w-4 h-4" />
          </Button>
        </div>

        {/* View tabs */}
        <div className="flex gap-1">
          {(['memories', 'conversations', 'facts'] as const).map((view) => (
            <Button
              key={view}
              variant={activeView === view ? 'default' : 'ghost'}
              size="sm"
              onClick={() => setActiveView(view)}
              className={`text-xs capitalize ${activeView === view ? 'bg-cyan-500/20 text-cyan-300' : 'text-white/50'}`}
            >
              {view}
            </Button>
          ))}
        </div>

        {/* Memories View */}
        {activeView === 'memories' && (
          <div className="space-y-2">
            {memories.length === 0 && (
              <p className="text-center text-white/30 text-sm py-8">No significant memories yet</p>
            )}
            {memories.map((m) => (
              <Card key={m.id} className="bg-white/5 border-white/10 p-3">
                {editingId === m.id ? (
                  <div className="space-y-2">
                    <Input
                      value={editTitle}
                      onChange={(e) => setEditTitle(e.target.value)}
                      className="bg-white/5 border-white/10 text-white text-sm h-7"
                    />
                    <textarea
                      value={editContent}
                      onChange={(e) => setEditContent(e.target.value)}
                      className="w-full bg-white/5 border border-white/10 rounded-md text-white text-sm p-2 min-h-[60px] resize-none"
                    />
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] text-white/40">Importance:</span>
                      <input
                        type="range"
                        min={1}
                        max={10}
                        value={editImportance}
                        onChange={(e) => setEditImportance(Number(e.target.value))}
                        className="flex-1"
                      />
                      <span className="text-xs text-white w-4">{editImportance}</span>
                    </div>
                    <div className="flex gap-1">
                      <Button onClick={saveEdit} size="sm" className="h-6 text-xs bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-300">
                        <Save className="w-3 h-3 mr-1" /> Save
                      </Button>
                      <Button onClick={() => setEditingId(null)} size="sm" variant="ghost" className="h-6 text-xs">
                        <X className="w-3 h-3 mr-1" /> Cancel
                      </Button>
                    </div>
                  </div>
                ) : (
                  <div>
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <h4 className="text-sm font-medium text-white">{m.title}</h4>
                          <Badge variant="outline" className="text-[9px] h-4 border-white/20 text-white/50">
                            {m.importance}/10
                          </Badge>
                        </div>
                        <p className="text-xs text-white/60 mt-0.5 line-clamp-2">{m.content}</p>
                        <p className="text-[10px] text-white/30 mt-1">{formatTime(m.timestamp)}</p>
                      </div>
                      <div className="flex gap-1 ml-2">
                        <Button onClick={() => startEdit(m)} size="sm" variant="ghost" className="h-6 w-6 p-0 text-white/40 hover:text-white">
                          <Edit2 className="w-3 h-3" />
                        </Button>
                        <Button onClick={() => deleteMemory(m.id)} size="sm" variant="ghost" className="h-6 w-6 p-0 text-white/40 hover:text-red-400">
                          <Trash2 className="w-3 h-3" />
                        </Button>
                      </div>
                    </div>
                  </div>
                )}
              </Card>
            ))}
          </div>
        )}

        {/* Conversations View */}
        {activeView === 'conversations' && (
          <div className="space-y-1 max-h-[400px]">
            {conversations.length === 0 && (
              <p className="text-center text-white/30 text-sm py-8">No conversations found</p>
            )}
            {conversations.slice(-50).reverse().map((c) => (
              <div key={c.id} className={`p-2 rounded-lg ${c.role === 'user' ? 'bg-rose-500/10' : c.role === 'system' ? 'bg-yellow-500/5' : 'bg-white/5'}`}>
                <div className="flex items-center gap-1.5 mb-0.5">
                  <Badge variant="outline" className={`text-[9px] h-4 capitalize ${c.role === 'user' ? 'border-rose-500/30 text-rose-300' : c.role === 'system' ? 'border-yellow-500/30 text-yellow-300' : 'border-cyan-500/30 text-cyan-300'}`}>
                    {c.role}
                  </Badge>
                  <span className="text-[9px] text-white/30">{formatTime(c.timestamp)}</span>
                </div>
                <p className="text-xs text-white/70 line-clamp-3">{c.content}</p>
              </div>
            ))}
          </div>
        )}

        {/* Facts View */}
        {activeView === 'facts' && (
          <div className="space-y-3">
            {Object.keys(facts).length === 0 && (
              <p className="text-center text-white/30 text-sm py-8">No facts stored yet</p>
            )}
            {Object.entries(facts).map(([category, items]) => (
              <div key={category}>
                <h4 className="text-xs font-semibold text-white/60 uppercase tracking-wider mb-1">{category}</h4>
                {items.map((item: any, i: number) => (
                  <div key={i} className="text-xs text-white/50 pl-2 border-l border-white/10 py-0.5">
                    {item.fact || item}
                  </div>
                ))}
              </div>
            ))}
          </div>
        )}
      </div>
    </ScrollArea>
  );
}
