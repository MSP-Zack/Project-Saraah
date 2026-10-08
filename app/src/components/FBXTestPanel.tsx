import { useCallback, useEffect, useState } from 'react';
import { Box, Play, RefreshCw, RotateCcw } from 'lucide-react';
import { FBXLoader } from 'three/addons/loaders/FBXLoader.js';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';

interface FBXFile {
  name: string;
  url: string;
  size: number;
}

interface FBXClip {
  id: string;
  fileName: string;
  fileUrl: string;
  name: string;
  duration: number;
}

export default function FBXTestPanel() {
  const [files, setFiles] = useState<FBXFile[]>([]);
  const [clips, setClips] = useState<FBXClip[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [activeClip, setActiveClip] = useState<string | null>(null);

  const scanFolder = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const response = await fetch('/api/fbx-tests');
      if (!response.ok) throw new Error(`Scanner returned ${response.status}`);
      const data = await response.json() as { files?: FBXFile[] };
      const nextFiles = data.files || [];
      setFiles(nextFiles);

      const loader = new FBXLoader();
      const discovered: FBXClip[] = [];
      await Promise.all(nextFiles.map((file) => new Promise<void>((resolve) => {
        loader.load(
          file.url,
          (object) => {
            object.animations.forEach((animation, index) => {
              discovered.push({
                id: `${file.name}:${index}:${animation.name || 'unnamed'}`,
                fileName: file.name,
                fileUrl: file.url,
                name: animation.name || `Animation ${index + 1}`,
                duration: animation.duration,
              });
            });
            resolve();
          },
          undefined,
          (loadError) => {
            console.warn(`[FBX TEST]: Failed to inspect ${file.name}`, loadError);
            resolve();
          },
        );
      })));
      setClips(discovered.sort((a, b) => a.fileName.localeCompare(b.fileName) || a.name.localeCompare(b.name)));
    } catch (scanError) {
      setError(scanError instanceof Error ? scanError.message : 'Unable to scan FBX folder');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    scanFolder();
  }, [scanFolder]);

  const playClip = (clip: FBXClip) => {
    setActiveClip(clip.id);
    window.dispatchEvent(new CustomEvent('fbx-animation-test', {
      detail: { url: clip.fileUrl, clipName: clip.name },
    }));
  };

  const clearPreview = () => {
    setActiveClip(null);
    window.dispatchEvent(new CustomEvent('fbx-animation-clear'));
  };

  const formatSize = (bytes: number) => `${(bytes / 1024 / 1024).toFixed(1)} MB`;
  const formatDuration = (seconds: number) => `${seconds.toFixed(2)}s`;

  return (
    <ScrollArea className="h-full px-4 py-4">
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Box className="h-5 w-5 text-amber-300" />
            <div>
              <h2 className="text-lg font-semibold text-white">FBX Tests</h2>
              <p className="text-[10px] text-white/40">Temporary animation preview tool</p>
            </div>
          </div>
          <Button onClick={scanFolder} disabled={loading} size="icon" variant="ghost" className="h-8 w-8 text-white/50 hover:text-white" title="Rescan FBX folder">
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          </Button>
        </div>

        <Card className="border-amber-400/20 bg-amber-500/5 p-3">
          <p className="text-xs leading-relaxed text-white/65">
            Put `.fbx` files in <span className="text-amber-200">sarah_ai/static/fbx_tests</span>, then rescan.
            The preview temporarily displays the selected FBX instead of Sarah's VRM.
          </p>
        </Card>

        {error && <p className="rounded-lg border border-red-400/20 bg-red-500/10 p-3 text-xs text-red-200">{error}</p>}

        <div className="flex items-center justify-between text-xs text-white/60">
          <span>{files.length} file{files.length === 1 ? '' : 's'} · {clips.length} animation{clips.length === 1 ? '' : 's'}</span>
          <Button onClick={clearPreview} size="sm" variant="ghost" className="h-7 gap-1 text-white/50 hover:text-white">
            <RotateCcw className="h-3 w-3" /> Clear preview
          </Button>
        </div>

        <div className="space-y-2">
          {clips.map((clip) => (
            <Card key={clip.id} className={`border-white/10 bg-white/5 p-3 ${activeClip === clip.id ? 'border-amber-300/50 bg-amber-400/10' : ''}`}>
              <div className="flex items-center justify-between gap-3">
                <div className="min-w-0">
                  <p className="truncate text-sm font-medium text-white">{clip.name}</p>
                  <p className="truncate text-[10px] text-white/40">{clip.fileName} · {formatDuration(clip.duration)}</p>
                </div>
                <Button onClick={() => playClip(clip)} size="icon" variant="ghost" className="h-8 w-8 shrink-0 text-amber-300 hover:bg-amber-400/10 hover:text-amber-200" title={`Play ${clip.name}`}>
                  <Play className="h-4 w-4" />
                </Button>
              </div>
            </Card>
          ))}
          {files.length > 0 && clips.length === 0 && !loading && (
            <p className="py-8 text-center text-sm text-white/35">Files found, but no animation clips were detected.</p>
          )}
          {files.length === 0 && !loading && (
            <p className="py-8 text-center text-sm text-white/35">No FBX files found. Add files to the test folder and rescan.</p>
          )}
        </div>

        {files.length > 0 && (
          <div className="space-y-1 text-[10px] text-white/35">
            {files.map((file) => <p key={file.name}>{file.name} · {formatSize(file.size)}</p>)}
          </div>
        )}
      </div>
    </ScrollArea>
  );
}
