import { useState, useEffect, useRef } from 'react';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { useStore } from '@/hooks/useStore';
import { UploadCloud, Play, Pause, StopCircle, FileText, DownloadCloud } from 'lucide-react';
import { Select, SelectContent, SelectItem, SelectGroup, SelectLabel, SelectTrigger, SelectValue, SelectSeparator } from '@/components/ui/select';

export default function EbooksPanel() {
  const store = useStore();
  const [ebooks, setEbooks] = useState<Record<string, any>>({});
  const [selected, setSelected] = useState<string | null>(null);
  const [meta, setMeta] = useState<any>(null);
  const [startPage, setStartPage] = useState<number | null>(1);
  const [endPage, setEndPage] = useState<number | null>(1);
  const [textPreview, setTextPreview] = useState<string>('');
  const [uploading, setUploading] = useState(false);
  const fileRef = useRef<HTMLInputElement | null>(null);
  const previewRef = useRef<HTMLTextAreaElement | null>(null);

  const [profiles, setProfiles] = useState<Record<string, any>>({});
  const [voices, setVoices] = useState<Record<string, any>>({});
  const [selectedProfile, setSelectedProfile] = useState<string | null>(null);
  const [speed, setSpeed] = useState<number>(1.0);

  const [generating, setGenerating] = useState(false);
  const [audioUrls, setAudioUrls] = useState<string[]>([]);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const currentIndex = useRef<number>(0);

  useEffect(() => {
    fetchList();
    fetchVoices();
  }, []);

  const fetchVoices = async () => {
    try {
      const res = await fetch('/api/tts/voices');
      const data = await res.json();
      setProfiles(data.profiles || {});
      setVoices(data.voices || {});
      setSelectedProfile(data.current || data.current || 'default');
    } catch (e) { console.error('Failed to fetch voices', e); }
  };

  const fetchList = async () => {
    try {
      const res = await fetch('/api/ebooks/list');
      const data = await res.json();
      setEbooks(data.ebooks || {});
    } catch (e) { console.error('Failed to list ebooks', e); }
  };

  const handleUpload = async () => {
    if (!fileRef.current?.files?.length) return alert('Choose a file');
    setUploading(true);
    try {
      const f = fileRef.current.files[0];
      const form = new FormData();
      form.append('file', f);
      const res = await fetch('/api/ebooks/upload', { method: 'POST', body: form });
      const data = await res.json();
      if (data.success) {
        alert('Uploaded');
        fetchList();
      } else alert('Upload failed: ' + (data.error || ''));
    } catch (e) { console.error(e); alert('Upload error'); }
    setUploading(false);
    if (fileRef.current) fileRef.current.value = '';
  };

  const selectEbook = async (id: string) => {
    setSelected(id);
    try {
      const res = await fetch(`/api/ebooks/meta/${id}`);
      const data = await res.json();
      if (data.success) {
        setMeta(data.meta);
        setStartPage(1);
        setEndPage(data.meta.pages || data.meta.chapters || 1);
      }
    } catch (e) { console.error('meta fetch failed', e); }
  };

  const previewText = async () => {
    if (!selected) return;
    try {
      const res = await fetch(`/api/ebooks/text/${selected}?start_page=${startPage || 1}&end_page=${endPage || startPage || 1}`);
      const data = await res.json();
      if (data.success) setTextPreview(data.text || '');
      else alert('Preview failed: ' + (data.error || ''));
    } catch (e) { console.error(e); }
  };

  const setStartFromSelection = () => {
    if (!previewRef.current) return alert('No preview available');
    const ta = previewRef.current;
    const selStart = ta.selectionStart || 0;
    if (!meta) return alert('No metadata to map selection to pages');
    try {
      const totalChars = (textPreview || '').length || 1;
      const pages = meta.pages || meta.chapters || 1;
      const charsPerPage = Math.max(1, Math.floor(totalChars / pages));
      const page = Math.max(1, Math.floor(selStart / charsPerPage) + 1);
      setStartPage(page);
      alert(`Start page set to ${page} (from selection)`);
    } catch (e) {
      console.error(e);
      alert('Failed to set start from selection');
    }
  };

  const readNow = async () => {
    if (!selected) return alert('Select an ebook');
    setGenerating(true);
    try {
      const form = new FormData();
      form.append('ebook_id', selected);
      form.append('start_page', String(startPage || 1));
      form.append('end_page', String(endPage || startPage || 1));
      // use selected profile if present, otherwise fallback to store profile
      form.append('profile', selectedProfile || store.voiceProfile || 'default');
      // convert speed multiplier to rate string like '+10%' or '-10%'
      const pct = Math.round((speed - 1.0) * 100);
      const rateStr = `${pct >= 0 ? '+' : ''}${pct}%`;
      form.append('rate', rateStr);
      const res = await fetch('/api/ebooks/read', { method: 'POST', body: form });
      const data = await res.json();
      if (data.success && data.audio_urls) {
        setAudioUrls(data.audio_urls);
        currentIndex.current = 0;
        setTimeout(() => playIndex(0), 100);
      } else alert('Read failed: ' + (data.error || ''));
    } catch (e) { console.error(e); alert('Error generating audio'); }
    setGenerating(false);
  };

  const playIndex = (idx: number) => {
    if (!audioRef.current) audioRef.current = document.createElement('audio');
    if (!audioUrls || audioUrls.length === 0) return;
    if (idx < 0 || idx >= audioUrls.length) return;
    currentIndex.current = idx;
    audioRef.current.src = audioUrls[idx] + '?t=' + Date.now();
    audioRef.current.onended = () => {
      if (currentIndex.current + 1 < audioUrls.length) playIndex(currentIndex.current + 1);
    };
    audioRef.current.play().catch(() => {});
  };

  const pause = () => audioRef.current?.pause();
  const stop = () => { if (audioRef.current) { audioRef.current.pause(); audioRef.current.currentTime = 0; } };

  return (
    <ScrollArea className="h-full px-4 py-4">
      <div className="space-y-4">
        <div className="flex items-center gap-2 mb-2">
          <FileText className="w-5 h-5 text-emerald-400" />
          <h2 className="text-lg font-semibold text-white">E‑Books</h2>
        </div>

        <Card className="bg-white/5 border-white/10 p-3">
          <div className="flex gap-2 items-center">
            <input ref={fileRef} type="file" accept=".pdf,.epub,.txt" className="hidden" />
            <Button onClick={() => fileRef.current?.click()} size="sm" className="flex items-center gap-2"><UploadCloud className="w-4 h-4" /> Choose</Button>
            <Button onClick={handleUpload} size="sm">{uploading ? 'Uploading...' : 'Upload'}</Button>
            <div className="ml-auto text-xs text-white/40">Supported: PDF, EPUB, TXT</div>
          </div>
        </Card>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <Card className="bg-white/5 border-white/10 p-3">
            <h3 className="text-sm text-white mb-2">Library</h3>
            <div className="space-y-2 max-h-96 overflow-auto">
              {Object.keys(ebooks).length === 0 && <div className="text-xs text-white/40">No ebooks uploaded</div>}
              {Object.entries(ebooks).map(([id, e]) => (
                <div key={id} className={`p-2 rounded-md cursor-pointer hover:bg-white/5 ${selected === id ? 'ring-1 ring-emerald-400' : ''}`} onClick={() => selectEbook(id)}>
                  <div className="text-sm text-white font-medium">{e.filename || e.stored_name || id}</div>
                  <div className="text-xs text-white/50">{e.ext?.toUpperCase()} • {Math.round((e.size || 0)/1024)} KB</div>
                </div>
              ))}
            </div>
          </Card>

          <Card className="bg-white/5 border-white/10 p-3">
            <h3 className="text-sm text-white mb-2">Details</h3>
            {meta ? (
              <div className="space-y-2 text-xs text-white/60">
                <div><strong className="text-white">{meta.title || meta.filename || meta.stored_name}</strong></div>
                <div>Author: {meta.author || 'Unknown'}</div>
                <div>Pages: {meta.pages || meta.chapters || '—'}</div>
                <div>Uploaded: {new Date(meta.uploaded_at || Date.now()).toLocaleString()}</div>
                <div className="mt-2 grid grid-cols-2 gap-2">
                  <Input value={String(startPage || '')} onChange={(e) => setStartPage(Number(e.target.value || 1))} />
                  <Input value={String(endPage || '')} onChange={(e) => setEndPage(Number(e.target.value || startPage || 1))} />
                </div>
                <div className="flex gap-2 mt-2">
                  <Button onClick={previewText} size="sm">Preview Text</Button>
                  <Button onClick={readNow} size="sm" className="bg-emerald-500/20 hover:bg-emerald-500/30">{generating ? 'Generating...' : 'Read'}</Button>
                </div>
              </div>
            ) : (
              <div className="text-xs text-white/40">Select an ebook to see details</div>
            )}
          </Card>

          <Card className="bg-white/5 border-white/10 p-3">
            <h3 className="text-sm text-white mb-2">Player</h3>
            <div className="text-xs text-white/60 mb-2">Voice / Speed</div>
            <div className="flex items-center gap-2 mb-3">
              <div className="flex-1">
                <Select value={selectedProfile || store.voiceProfile} onValueChange={(v) => setSelectedProfile(v)}>
                  <SelectTrigger className="bg-white/5 border-white/10 text-white w-full h-8">
                    <SelectValue placeholder="Select voice/profile" />
                  </SelectTrigger>
                  <SelectContent className="bg-gray-900 border-white/20">
                    <SelectGroup>
                      <SelectLabel>Profiles</SelectLabel>
                      {Object.keys(profiles).length > 0 ? (
                        Object.keys(profiles).map((p) => <SelectItem key={p} value={p}>{p}</SelectItem>)
                      ) : (
                        <SelectItem value="default">default</SelectItem>
                      )}
                    </SelectGroup>
                    <SelectSeparator />
                    <SelectGroup>
                      <SelectLabel>Voices</SelectLabel>
                      {Object.keys(voices).length > 0 ? (
                        Object.keys(voices).map((v) => <SelectItem key={v} value={v}>{v}</SelectItem>)
                      ) : null}
                    </SelectGroup>
                  </SelectContent>
                </Select>
              </div>

              <div className="w-36">
                <div className="text-xs text-white/50 mb-1">Speed: {speed}x</div>
                <input type="range" min={0.5} max={2.0} step={0.05} value={speed} onChange={(e) => setSpeed(Number(e.target.value))} />
              </div>
            </div>
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <Button onClick={() => playIndex(currentIndex.current)} size="sm"><Play className="w-4 h-4" /></Button>
                <Button onClick={pause} size="sm"><Pause className="w-4 h-4" /></Button>
                <Button onClick={stop} size="sm"><StopCircle className="w-4 h-4" /></Button>
              </div>

              <div className="text-xs text-white/50">{audioUrls.length} audio segment(s) ready</div>
              <div className="space-y-1">
                {audioUrls.map((u, i) => (
                  <div key={u} className="flex items-center justify-between text-xs text-white/60">
                    <div>Segment {i+1}</div>
                    <div className="flex items-center gap-2">
                      <a href={u} target="_blank" rel="noreferrer" className="text-white/60 hover:text-white"><DownloadCloud className="w-4 h-4" /></a>
                      <Button size="sm" onClick={() => playIndex(i)}>Play</Button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </Card>
        </div>

        <Card className="bg-white/5 border-white/10 p-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm text-white mb-2">Preview</h3>
            <div className="flex items-center gap-2">
              <Button size="sm" onClick={setStartFromSelection}>Set start from selection</Button>
              <Button size="sm" onClick={() => { setTextPreview(''); }}>Clear</Button>
            </div>
          </div>
          <textarea
            ref={previewRef}
            value={textPreview}
            onChange={(e) => setTextPreview(e.target.value)}
            className="min-h-[160px] w-full bg-transparent border border-white/10 rounded-md p-2 text-sm text-white placeholder:text-white/50"
          />
        </Card>
      </div>
    </ScrollArea>
  );
}
