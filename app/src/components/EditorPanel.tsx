import { useState, useEffect } from 'react';
import { useStore } from '@/hooks/useStore';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { FileText, Plus, Check, X, Edit3 } from 'lucide-react';

export default function EditorPanel() {
  const store = useStore();
  const [title, setTitle] = useState('');
  const [showNewDoc, setShowNewDoc] = useState(false);
  const [suggestionText, setSuggestionText] = useState('');
  const [suggestionExplain, setSuggestionExplain] = useState('');

  useEffect(() => {
    fetchDocuments();
  }, []);

  const fetchDocuments = async () => {
    try {
      const res = await fetch('/api/editor/documents');
      const data = await res.json();
      store.setDocuments(data.documents || []);
    } catch (e) {}
  };

  const createDocument = async () => {
    try {
      const res = await fetch(`/api/editor/new?title=${encodeURIComponent(title || 'Untitled')}`, {
        method: 'POST'
      });
      const data = await res.json();
      if (data.document) {
        store.setActiveDocument(data.document);
        store.setEditorContent(data.document.content);
        fetchDocuments();
        setShowNewDoc(false);
        setTitle('');
      }
    } catch (e) {}
  };

  const loadDocument = async (docId: string) => {
    try {
      const res = await fetch(`/api/editor/load?doc_id=${docId}`, { method: 'POST' });
      const data = await res.json();
      if (data.document) {
        store.setActiveDocument(data.document);
        store.setEditorContent(data.document.content);
      }
    } catch (e) {}
  };

  const handleUserType = async (text: string) => {
    if (!store.activeDocument) return;
    try {
      await fetch(`/api/editor/type?text=${encodeURIComponent(text)}`, { method: 'POST' });
      store.setEditorContent(store.editorContent + text);
    } catch (e) {}
  };

  const handleEditorChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const newContent = e.target.value;
    const diff = newContent.slice(store.editorContent.length);
    if (diff) {
      handleUserType(diff);
    } else {
      store.setEditorContent(newContent);
    }
  };

  const sarahSuggest = async () => {
    if (!suggestionText.trim()) return;
    const ws = (window as any).sarahWS;
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({
        type: 'editor_action',
        editor_action: 'sarah_suggest',
        text: suggestionText,
        explanation: suggestionExplain
      }));
    }
    setSuggestionText('');
    setSuggestionExplain('');
  };

  return (
    <div className="h-full flex flex-col px-4 py-4">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Edit3 className="w-5 h-5 text-emerald-400" />
          <h2 className="text-lg font-semibold text-white">Collaborative Editor</h2>
        </div>
        <Button onClick={() => setShowNewDoc(!showNewDoc)} size="sm" className="bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-300 border border-emerald-500/30">
          <Plus className="w-3 h-3 mr-1" /> New
        </Button>
      </div>

      {/* New doc form */}
      {showNewDoc && (
        <Card className="bg-white/5 border-white/10 p-3 mb-3">
          <div className="flex gap-2">
            <Input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Document title..."
              className="bg-white/5 border-white/10 text-white text-sm h-8"
              onKeyDown={(e) => e.key === 'Enter' && createDocument()}
            />
            <Button onClick={createDocument} size="sm" className="h-8 bg-emerald-500/20 text-emerald-300">Create</Button>
          </div>
        </Card>
      )}

      {!store.activeDocument ? (
        /* Document list */
        <ScrollArea className="flex-1">
          <div className="space-y-2">
            {store.documents.length === 0 && (
              <div className="text-center text-white/30 py-12">
                <FileText className="w-10 h-10 mx-auto mb-2 opacity-30" />
                <p className="text-sm">No documents yet</p>
                <p className="text-xs">Create one to start writing with Sarah</p>
              </div>
            )}
            {store.documents.map((doc) => (
              <Card
                key={doc.id}
                onClick={() => loadDocument(doc.id)}
                className="bg-white/5 border-white/10 p-3 cursor-pointer hover:bg-white/10 transition-colors"
              >
                <h4 className="text-sm font-medium text-white">{doc.title}</h4>
                <p className="text-xs text-white/40 mt-0.5 line-clamp-1">{doc.preview}</p>
                <p className="text-[10px] text-white/20 mt-1">
                  {new Date(doc.modified).toLocaleDateString()}
                </p>
              </Card>
            ))}
          </div>
        </ScrollArea>
      ) : (
        /* Active editor */
        <div className="flex-1 flex flex-col">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-medium text-white">{store.activeDocument.title}</h3>
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="text-[9px] h-5 border-cyan-500/30 text-cyan-300">
                <FileText className="w-3 h-3 mr-1" /> {store.editorContent.length} chars
              </Badge>
              <Button onClick={() => store.setActiveDocument(null)} size="sm" variant="ghost" className="h-6 w-6 p-0 text-white/40">
                <X className="w-4 h-4" />
              </Button>
            </div>
          </div>

          {/* Cursors indicator */}
          <div className="flex items-center gap-3 mb-2">
            <div className="flex items-center gap-1">
              <div className="w-2 h-2 rounded-full bg-rose-500" />
              <span className="text-[10px] text-white/40">You</span>
            </div>
            <div className="flex items-center gap-1">
              <div className="w-2 h-2 rounded-full bg-cyan-500" />
              <span className="text-[10px] text-white/40">Sarah</span>
            </div>
          </div>

          <textarea
            value={store.editorContent}
            onChange={handleEditorChange}
            className="flex-1 bg-white/5 border border-white/10 rounded-lg p-3 text-sm text-white resize-none focus:border-cyan-500/50 focus:outline-none"
            placeholder="Start typing... Sarah can write here too!"
          />

          {/* Suggestion input */}
          <Card className="bg-white/5 border-white/10 p-2 mt-2">
            <p className="text-[10px] text-white/40 mb-1">Ask Sarah to write something:</p>
            <div className="flex gap-1.5">
              <Input
                value={suggestionText}
                onChange={(e) => setSuggestionText(e.target.value)}
                placeholder="e.g., Write an introduction..."
                className="bg-white/5 border-white/10 text-white text-xs h-7"
                onKeyDown={(e) => e.key === 'Enter' && sarahSuggest()}
              />
              <Button onClick={sarahSuggest} size="sm" className="h-7 bg-cyan-500/20 text-cyan-300 text-xs px-2">
                <Check className="w-3 h-3" />
              </Button>
            </div>
          </Card>

          {/* Suggestions */}
          {store.activeDocument.suggestions && store.activeDocument.suggestions.length > 0 && (
            <div className="mt-2 space-y-1">
              {store.activeDocument.suggestions.filter((s: any) => s.accepted === null).map((s: any) => (
                <Card key={s.id} className="bg-cyan-500/5 border-cyan-500/20 p-2">
                  <p className="text-xs text-cyan-200">{s.text}</p>
                  <p className="text-[10px] text-white/40">{s.explanation}</p>
                  <div className="flex gap-1 mt-1">
                    <Button onClick={() => {/* accept */}} size="sm" className="h-5 text-[10px] bg-green-500/20 text-green-300 px-2">Accept</Button>
                    <Button onClick={() => {/* reject */}} size="sm" variant="ghost" className="h-5 text-[10px] text-white/40 px-2">Reject</Button>
                  </div>
                </Card>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
