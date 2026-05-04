import { useEffect, useState } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { Loader2, Search, Download, Sparkles } from 'lucide-react';

interface ImageResult {
  id: string;
  title: string;
  thumbnail: string;
  url: string;
  source: string;
}

interface HistoryEntry {
  id: string;
  type: string;
  query?: string;
  prompt?: string;
  images?: string[];
  url?: string;
  timestamp: string;
}

export default function ImagePanel() {
  const [activeTab, setActiveTab] = useState<'search' | 'generate' | 'saved' | 'history'>('search');
  const [query, setQuery] = useState('cute robot');
  const [prompt, setPrompt] = useState('A futuristic anime-style companion robot with soft lighting');
  const [source, setSource] = useState('bing');
  const [results, setResults] = useState<ImageResult[]>([]);
  const [savedImages, setSavedImages] = useState<string[]>([]);
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState('');
  const [selectedImage, setSelectedImage] = useState<ImageResult | null>(null);

  useEffect(() => {
    loadSavedImages();
    loadHistory();
  }, []);

  const loadSavedImages = async () => {
    try {
      const res = await fetch('/api/images/list');
      const data = await res.json();
      if (data.images) {
        setSavedImages(data.images);
      }
    } catch (error) {
      console.error('Failed to load saved images:', error);
    }
  };

  const loadHistory = async () => {
    try {
      const res = await fetch('/api/images/history');
      const data = await res.json();
      if (data.history) {
        setHistory(data.history);
      }
    } catch (error) {
      console.error('Failed to load image history:', error);
    }
  };

  const searchImages = async () => {
    if (!query.trim()) return;
    setLoading(true);
    setStatus('Searching images...');
    try {
      const res = await fetch(`/api/images/search?query=${encodeURIComponent(query)}&source=${encodeURIComponent(source)}&limit=18`);
      const data = await res.json();
      if (data.success) {
        setResults(data.results || []);
      } else {
        setStatus(data.error || 'Search failed');
      }
    } catch (error) {
      console.error('Image search failed:', error);
      setStatus('Search failed. Try again.');
    } finally {
      setLoading(false);
    }
  };

  const generateImage = async () => {
    if (!prompt.trim()) return;
    setLoading(true);
    setStatus('Generating image...');
    try {
      const res = await fetch('/api/images/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt, style: 'creative', count: 1 })
      });
      const data = await res.json();
      if (data.success && Array.isArray(data.images)) {
        setSavedImages((prev) => [...data.images, ...prev]);
        setHistory((prev) => [{
          id: Date.now().toString(),
          type: 'generate',
          prompt,
          images: data.images,
          timestamp: new Date().toISOString(),
        }, ...prev]);
        setStatus('Image generated successfully.');
      } else {
        setStatus(data.error || 'Generation failed');
      }
    } catch (error) {
      console.error('Image generation failed:', error);
      setStatus('Image generation failed.');
    } finally {
      setLoading(false);
    }
  };

  const downloadImage = async (imageUrl: string) => {
    setLoading(true);
    setStatus('Downloading image...');
    try {
      const res = await fetch('/api/images/download', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: imageUrl })
      });
      const data = await res.json();
      if (data.success && data.url) {
        setSavedImages((prev) => [data.url, ...prev]);
        setStatus('Image downloaded.');
      } else {
        setStatus(data.error || 'Download failed');
      }
    } catch (error) {
      console.error('Download failed:', error);
      setStatus('Download failed.');
    } finally {
      setLoading(false);
    }
  };

  const renderImageCard = (image: ImageResult) => (
    <Card
      key={image.id}
      className="bg-white/5 border-white/10 cursor-pointer overflow-hidden transition hover:border-cyan-400/40"
      onClick={() => setSelectedImage(image)}
    >
      <div className="relative overflow-hidden rounded-xl bg-slate-950/20">
        <img src={image.thumbnail || image.url} alt={image.title} className="h-40 w-full object-cover" />
      </div>
      <div className="p-3 space-y-2">
        <div className="flex items-center justify-between gap-2">
          <p className="text-sm font-semibold text-white truncate">{image.title || 'Image result'}</p>
          <Badge className="text-[10px] bg-white/10 text-white/70 border-white/10 uppercase">{image.source}</Badge>
        </div>
        <p className="text-xs text-white/40 line-clamp-2">{image.url}</p>
      </div>
    </Card>
  );

  return (
    <ScrollArea className="h-full px-4 py-4">
      <div className="space-y-4">
        <div className="flex items-center gap-2 mb-3">
          <Sparkles className="w-5 h-5 text-cyan-400" />
          <h2 className="text-lg font-semibold text-white">Image Studio</h2>
        </div>

        <div className="flex flex-wrap gap-2">
          {(['search', 'generate', 'saved', 'history'] as const).map((tab) => (
            <Button
              key={tab}
              size="sm"
              variant={activeTab === tab ? 'secondary' : 'ghost'}
              className={activeTab === tab ? 'bg-cyan-500/20 text-white' : 'bg-white/5 text-white/70'}
              onClick={() => setActiveTab(tab)}
            >
              {tab === 'search' && 'Search'}
              {tab === 'generate' && 'Generate'}
              {tab === 'saved' && 'Saved'}
              {tab === 'history' && 'History'}
            </Button>
          ))}
        </div>

        <Card className="bg-white/5 border-white/10 p-4 space-y-4">
          {activeTab === 'search' && (
            <div className="space-y-4">
              <div className="grid gap-3 md:grid-cols-[1fr_140px]">
                <Input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search for images..." />
                <Button onClick={searchImages} disabled={loading}>
                  {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <><Search className="w-4 h-4 mr-2" /> Search</>}
                </Button>
              </div>
              <div className="flex flex-wrap gap-2 text-xs text-white/50">
                <Button variant="ghost" onClick={() => setSource('bing')} className={source === 'bing' ? 'bg-cyan-500/20' : ''}>Bing</Button>
                <Button variant="ghost" onClick={() => setSource('unsplash')} className={source === 'unsplash' ? 'bg-cyan-500/20' : ''}>Unsplash</Button>
                <Button variant="ghost" onClick={() => setSource('pexels')} className={source === 'pexels' ? 'bg-cyan-500/20' : ''}>Pexels</Button>
              </div>
            </div>
          )}

          {activeTab === 'generate' && (
            <div className="space-y-4">
              <Textarea
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="Describe the image to generate..."
                className="min-h-[140px] bg-white/5 border-white/10 text-white placeholder:text-white/30"
              />
              <div className="flex flex-wrap gap-2 items-center">
                <Button onClick={generateImage} disabled={loading}>
                  {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <><Sparkles className="w-4 h-4 mr-2" /> Generate</>}
                </Button>
                <p className="text-xs text-white/40">Create quick placeholder art from your prompt.</p>
              </div>
            </div>
          )}

          {activeTab === 'saved' && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-semibold text-white">Saved Images</h3>
                  <p className="text-xs text-white/50">Images Sarah generated or downloaded.</p>
                </div>
                <Button size="sm" variant="outline" onClick={loadSavedImages}>Refresh</Button>
              </div>
              {savedImages.length === 0 ? (
                <p className="text-sm text-white/50">No saved images yet. Generate or download one to get started.</p>
              ) : (
                <div className="grid gap-3 md:grid-cols-2">
                  {savedImages.map((url) => (
                    <Card key={url} className="bg-white/5 border-white/10 overflow-hidden">
                      <img src={url} alt="Saved asset" className="h-40 w-full object-cover" />
                      <div className="p-3 flex items-center justify-between gap-2">
                        <span className="text-xs text-white/60 truncate">{url.replace('/static/generated_images/', '')}</span>
                        <Button size="sm" variant="ghost" onClick={() => window.open(url, '_blank')}>View</Button>
                      </div>
                    </Card>
                  ))}
                </div>
              )}
            </div>
          )}

          {activeTab === 'history' && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-semibold text-white">History</h3>
                  <p className="text-xs text-white/50">Recent image searches and generations.</p>
                </div>
                <Button size="sm" variant="outline" onClick={loadHistory}>Refresh</Button>
              </div>
              {history.length === 0 ? (
                <p className="text-sm text-white/50">No image history yet.</p>
              ) : (
                <div className="space-y-3">
                  {history.map((entry) => (
                    <Card key={entry.id} className="bg-white/5 border-white/10 p-3">
                      <div className="flex items-center justify-between gap-2">
                        <div>
                          <p className="text-xs text-white/70 uppercase tracking-[0.2em]">{entry.type}</p>
                          <p className="text-sm text-white">{entry.prompt || entry.query || entry.url || 'Image operation'}</p>
                        </div>
                        <Badge className="bg-white/10 text-white/70 border-white/10 text-xs">{new Date(entry.timestamp).toLocaleString()}</Badge>
                      </div>
                      {entry.images && entry.images.length > 0 && (
                        <div className="mt-2 grid gap-2 sm:grid-cols-2">
                          {entry.images.map((imageUrl) => (
                            <img key={imageUrl} src={imageUrl} alt="History" className="h-24 w-full rounded-md object-cover" />
                          ))}
                        </div>
                      )}
                    </Card>
                  ))}
                </div>
              )}
            </div>
          )}

          {status && (
            <div className="rounded-xl border border-white/10 bg-black/40 p-3 text-sm text-white/70">{status}</div>
          )}
        </Card>

        {activeTab === 'search' && results.length > 0 && (
          <div className="space-y-3">
            <div className="flex items-center gap-2 text-xs text-white/50">
              <Search className="w-4 h-4" />
              <span>Search results</span>
            </div>
            <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
              {results.map(renderImageCard)}
            </div>
          </div>
        )}

        {selectedImage && (
          <Card className="bg-white/5 border-white/10 p-4 space-y-3">
            <div className="flex items-center justify-between gap-2">
              <div>
                <h3 className="text-sm font-semibold text-white">Preview</h3>
                <p className="text-xs text-white/40">Click download to save the selected image.</p>
              </div>
              <Badge className="bg-white/10 text-white/70 border-white/10">{selectedImage.source}</Badge>
            </div>
            <img src={selectedImage.thumbnail || selectedImage.url} alt={selectedImage.title} className="h-72 w-full rounded-xl object-cover" />
            <div className="flex flex-wrap gap-2">
              <Button onClick={() => downloadImage(selectedImage.url)} disabled={loading}>
                <Download className="w-4 h-4 mr-2" /> Save Image
              </Button>
              <Button variant="secondary" onClick={() => setSelectedImage(null)}>
                Close
              </Button>
            </div>
          </Card>
        )}
      </div>
    </ScrollArea>
  );
}
