import { useStore } from '@/hooks/useStore';
import { useState, useEffect, useRef } from 'react';
import { getWebSocket } from '@/hooks/useWebSocket';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Textarea } from '@/components/ui/textarea';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectGroup, SelectLabel, SelectTrigger, SelectValue, SelectSeparator } from '@/components/ui/select';
import { Card } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import { Settings, Brain, MessageCircle, Volume2, Eye, Sparkles } from 'lucide-react';
import { Input } from '@/components/ui/input';

export default function SettingsPanel() {
  const store = useStore();
  const [profiles, setProfiles] = useState<Record<string, any>>({});
  const [voices, setVoices] = useState<Record<string, any>>({});
  const [customVoices, setCustomVoices] = useState<Record<string, any>>({});
  const [provider, setProvider] = useState<string>(localStorage.getItem('tts_provider') || 'edge_tts');
  const [search, setSearch] = useState<string>('');
  const [uploading, setUploading] = useState(false);
  const [sampleName, setSampleName] = useState('');
  const fileRef = useRef<HTMLInputElement | null>(null);
  const [notificationsEnabled, setNotificationsEnabled] = useState<boolean>(typeof Notification !== 'undefined' && Notification.permission === 'granted');

  const [imageProvider, setImageProvider] = useState<string>('huggingface');
  const [imageModel, setImageModel] = useState<string>('FLUX_DEV');
  const [imageQuality, setImageQuality] = useState<string>('STANDARD');
  const [imageSaveImages, setImageSaveImages] = useState<boolean>(true);
  const [imageSfwOnly, setImageSfwOnly] = useState<boolean>(true);
  const [imageAllowSarahGeneration, setImageAllowSarahGeneration] = useState<boolean>(true);
  const [huggingfaceApiKey, setHuggingfaceApiKey] = useState<string>('');
  const [replicateApiKey, setReplicateApiKey] = useState<string>('');
  const [localComfyUIUrl, setLocalComfyUIUrl] = useState<string>('');
  const [availableProviders, setAvailableProviders] = useState<string[]>([]);
  const [availableModels, setAvailableModels] = useState<string[]>([]);
  const [availableQualities, setAvailableQualities] = useState<string[]>([]);
  const [imageSettingsLoaded, setImageSettingsLoaded] = useState<boolean>(false);

  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const res = await fetch('/api/tts/voices');
        const data = await res.json();
        if (mounted && data) {
          setProfiles(data.profiles || {});
          setVoices(data.voices || {});
          setCustomVoices(data.custom_voices || {});
          if (data.current) store.setVoiceProfile(data.current);
        }
      } catch (e) {
        // ignore
      }
    })();
    return () => { mounted = false };
  }, []);

  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const res = await fetch('/api/images/settings');
        const data = await res.json();
        if (mounted && data?.success) {
          setImageProvider(data.provider || 'huggingface');
          setImageModel(data.model || 'FLUX_DEV');
          setImageQuality(data.default_quality || 'STANDARD');
          setImageSaveImages(data.save_images ?? true);
          setImageSfwOnly(data.sfw_only ?? true);
          setImageAllowSarahGeneration(data.allow_sarah_generation ?? true);
          setHuggingfaceApiKey(data.huggingface_api_key || '');
          setReplicateApiKey(data.replicate_api_key || '');
          setLocalComfyUIUrl(data.local_comfyui_url || '');
          setAvailableProviders(data.available_providers || []);
          setAvailableModels(data.available_models || []);
          setAvailableQualities(data.available_qualities || []);
          setImageSettingsLoaded(true);
        }
      } catch (e) {
        console.error('Failed to load image settings', e);
      }
    })();

    return () => { mounted = false };
  }, []);

  const saveImageSettings = async (updates: any) => {
    try {
      const res = await fetch('/api/images/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updates),
      });
      const data = await res.json();
      if (data.success) {
        if (updates.provider) setImageProvider(updates.provider);
        if (updates.model) setImageModel(updates.model);
        if (updates.default_quality) setImageQuality(updates.default_quality);
        if (typeof updates.save_images !== 'undefined') setImageSaveImages(updates.save_images);
        if (typeof updates.sfw_only !== 'undefined') setImageSfwOnly(updates.sfw_only);
        if (typeof updates.allow_sarah_generation !== 'undefined') setImageAllowSarahGeneration(updates.allow_sarah_generation);
        if (typeof updates.huggingface_api_key !== 'undefined') setHuggingfaceApiKey(updates.huggingface_api_key);
        if (typeof updates.replicate_api_key !== 'undefined') setReplicateApiKey(updates.replicate_api_key);
        if (typeof updates.local_comfyui_url !== 'undefined') setLocalComfyUIUrl(updates.local_comfyui_url);
      }
      return data;
    } catch (e) {
      console.error('Failed to save image settings', e);
      return { success: false, error: 'Unable to save image settings' };
    }
  };

  const sendConfig = (updates: any) => {
    const ws = getWebSocket();
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: 'config_update', config: updates }));
    }
  };

  const handleSystemPromptChange = (value: string) => {
    store.setSystemPrompt(value);
  };

  const handleSavePrompt = () => {
    sendConfig({ system_prompt: store.systemPrompt });
  };

  const requestNotificationPermission = async () => {
    if (typeof Notification === 'undefined') return alert('Notifications are not supported in this environment');
    if (Notification.permission === 'granted') return setNotificationsEnabled(true);
    const perm = await Notification.requestPermission();
    setNotificationsEnabled(perm === 'granted');
  };

  const enableBackgroundAudio = () => {
    try {
      // Creating/resuming an AudioContext on user gesture allows audio playback in background tabs in many browsers
      // We store it on window so other parts of the app can reuse it for TTS playback.
      const w = window as any;
      if (!w.__sarah_audio_ctx) {
        const AudioCtx = (window.AudioContext || (window as any).webkitAudioContext);
        if (!AudioCtx) return alert('AudioContext not supported in this browser');
        w.__sarah_audio_ctx = new AudioCtx();
      }
      if (w.__sarah_audio_ctx.state === 'suspended') w.__sarah_audio_ctx.resume();
      alert('Background audio enabled. TTS playback will use the shared audio context when available.');
    } catch (e) {
      console.error('Failed to enable background audio', e);
      alert('Failed to enable background audio');
    }
  };

  return (
    <ScrollArea className="h-full px-4 py-4">
      <div className="space-y-5">
        <div className="flex items-center gap-2 mb-4">
          <Settings className="w-5 h-5 text-cyan-400" />
          <h2 className="text-lg font-semibold text-white">Settings</h2>
        </div>

        {/* Personality / System Prompt */}
        <Card className="bg-white/5 border-white/10 p-4 space-y-3">
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-yellow-400" />
            <h3 className="text-sm font-medium text-white">Personality & System Prompt</h3>
          </div>
          <p className="text-xs text-white/50">Customize Sarah's personality and behavior</p>
          <Textarea
            value={store.systemPrompt}
            onChange={(e) => handleSystemPromptChange(e.target.value)}
            placeholder="Enter custom system prompt..."
            className="min-h-[120px] bg-white/5 border-white/10 text-white placeholder:text-white/30 text-sm resize-none"
          />
          <Button onClick={handleSavePrompt} size="sm" className="bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-300 border border-cyan-500/30">
            Save Personality
          </Button>
        </Card>

        {/* Voice Profile */}
        <Card className="bg-white/5 border-white/10 p-4 space-y-3">
          <div className="flex items-center gap-2">
            <Volume2 className="w-4 h-4 text-pink-400" />
            <h3 className="text-sm font-medium text-white">Voice Profile</h3>
          </div>

          <div className="flex flex-col md:flex-row md:items-center md:gap-4 gap-3">
            <div className="flex-1">
              <Select
                value={store.voiceProfile}
                onValueChange={(value) => {
                  store.setVoiceProfile(value);
                  const ws = getWebSocket();
                  if (ws && ws.readyState === WebSocket.OPEN) {
                    ws.send(JSON.stringify({ type: 'voice_profile', profile: value }));
                  }
                }}
              >
                <SelectTrigger className="bg-white/5 border-white/10 text-white w-full">
                  <SelectValue placeholder="Select voice or profile" />
                </SelectTrigger>
                <SelectContent className="bg-gray-900 border-white/20">
                  <div className="p-2">
                    <Input
                      placeholder="Search profiles, voices, custom..."
                      value={search}
                      onChange={(e) => setSearch((e.target as HTMLInputElement).value)}
                      className="mb-2"
                    />
                  </div>

                  <SelectGroup>
                    <SelectLabel>Presets</SelectLabel>
                    {Object.keys(profiles).length > 0 ? (
                      Object.keys(profiles)
                        .filter((k) => k.toLowerCase().includes(search.toLowerCase()))
                        .map((key) => (
                          <SelectItem key={key} value={key}>{key.charAt(0).toUpperCase() + key.slice(1)}</SelectItem>
                        ))
                    ) : (
                      <>
                        <SelectItem value="default">Sarah Cute (Default)</SelectItem>
                        <SelectItem value="excited">Excited</SelectItem>
                        <SelectItem value="shy">Shy</SelectItem>
                        <SelectItem value="tsundere">Tsundere</SelectItem>
                        <SelectItem value="gentle">Gentle</SelectItem>
                      </>
                    )}
                  </SelectGroup>

                  <SelectSeparator />

                  <SelectGroup>
                    <SelectLabel>Voices</SelectLabel>
                    {Object.keys(voices).length > 0 ? (
                      Object.keys(voices).filter((v) => v.toLowerCase().includes(search.toLowerCase())).map((v) => (
                        <SelectItem key={v} value={v}>{v.replace(/_/g, ' ')}</SelectItem>
                      ))
                    ) : null}
                  </SelectGroup>

                  <SelectSeparator />

                  <SelectGroup>
                    <SelectLabel>Custom Voices</SelectLabel>
                    {Object.keys(customVoices).length > 0 ? (
                      Object.keys(customVoices).filter((id) => (customVoices[id].name || id).toLowerCase().includes(search.toLowerCase())).map((id) => (
                        <SelectItem key={id} value={`custom:${id}`}>{customVoices[id].name || id}</SelectItem>
                      ))
                    ) : (
                      <SelectItem value="">No custom voices</SelectItem>
                    )}
                  </SelectGroup>
                </SelectContent>
              </Select>
            </div>

            <div className="flex items-center gap-2">
              <Button
                size="sm"
                variant="outline"
                onClick={async () => {
                  try {
                    const res = await fetch(`/api/tts/preview?profile=${encodeURIComponent(store.voiceProfile)}`);
                    const data = await res.json();
                    const url = data.preview_url || data.preview || '/static/preview.mp3';
                    if (data.success && url) {
                      const audio = new Audio(url + '?t=' + Date.now());
                      audio.play().catch(() => {});
                    }
                  } catch (e) {
                    console.error('Preview failed', e);
                  }
                }}
              >
                Preview
              </Button>

              <div className="ml-2 text-xs text-white/60">Provider:</div>
              <Select value={provider} onValueChange={(v) => { setProvider(v); localStorage.setItem('tts_provider', v); }}>
                <SelectTrigger className="bg-white/5 border-white/10 text-white h-8 w-48">
                  <SelectValue placeholder="Provider" />
                </SelectTrigger>
                <SelectContent className="bg-gray-900 border-white/20">
                  <SelectItem value="edge_tts">Edge (local)</SelectItem>
                  <SelectItem value="resemble">Resemble.ai (cloud)</SelectItem>
                  <SelectItem value="coqui">Coqui (self-host)</SelectItem>
                  <SelectItem value="none">None / Manual</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Upload / register custom voice sample */}
          <div className="mt-3 grid grid-cols-1 md:grid-cols-3 gap-2 items-center">
            <Input placeholder="Sample display name (e.g. Alex Waifu)" value={sampleName} onChange={(e) => setSampleName((e.target as HTMLInputElement).value)} className="md:col-span-2" />
            <input ref={fileRef} type="file" accept="audio/*" className="hidden" />
            <div className="flex items-center gap-2 md:col-span-1">
              <Button size="sm" onClick={() => fileRef.current?.click()} className="w-full">Choose File</Button>
              <Button size="sm" onClick={async () => {
                if (!fileRef.current?.files?.length) return alert('Please choose a file');
                if (!sampleName) return alert('Please enter a display name for the sample');
                setUploading(true);
                try {
                  const form = new FormData();
                  form.append('display_name', sampleName);
                  form.append('file', fileRef.current.files[0]);
                  const res = await fetch('/api/tts/clone', { method: 'POST', body: form });
                  const data = await res.json();
                  if (data.success) {
                    // Refresh voices list
                    const vs = await (await fetch('/api/tts/voices')).json();
                    setCustomVoices(vs.custom_voices || {});
                    alert('Sample uploaded and registered. It appears in Custom Voices.');
                    setSampleName('');
                    if (fileRef.current) fileRef.current.value = '';
                  } else {
                    alert('Upload failed: ' + (data.error || 'unknown'));
                  }
                } catch (e) {
                  console.error('Upload error', e);
                  alert('Upload failed');
                } finally {
                  setUploading(false);
                }
              }} disabled={uploading}>{uploading ? 'Uploading...' : 'Upload'}</Button>
            </div>
          </div>

          {/* Custom voice management */}
          <div className="mt-3 space-y-2">
            <div className="flex items-center justify-between">
              <div className="text-xs text-white/60">Custom Voices</div>
              <div className="text-xs text-white/40">Manage your uploaded samples</div>
            </div>
            <div className="grid grid-cols-1 gap-2">
              {Object.keys(customVoices).length > 0 ? (
                Object.keys(customVoices).map((id) => (
                  <div key={id} className="flex items-center justify-between bg-white/3 p-2 rounded-md border border-white/10">
                    <div>
                      <div className="text-sm text-white">{customVoices[id].name || id}</div>
                      <div className="text-xs text-white/50">{customVoices[id].path ? customVoices[id].path.split('/').slice(-1)[0] : ''}</div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Button size="sm" onClick={async () => {
                        try {
                          // set as active custom voice
                          const ws = getWebSocket();
                          if (ws && ws.readyState === WebSocket.OPEN) {
                            ws.send(JSON.stringify({ type: 'voice_profile', profile: `custom:${id}` }));
                          }
                          store.setVoiceProfile(`custom:${id}`);
                        } catch (e) { console.error(e); }
                      }}>Use</Button>
                      <Button size="sm" variant="destructive" onClick={async () => {
                        if (!confirm('Delete this custom voice sample?')) return;
                        try {
                          const res = await fetch(`/api/tts/custom/${id}`, { method: 'DELETE' });
                          const data = await res.json();
                          if (data.success) {
                            const vs = await (await fetch('/api/tts/voices')).json();
                            setCustomVoices(vs.custom_voices || {});
                          } else alert('Failed to delete');
                        } catch (e) { console.error(e); alert('Error deleting'); }
                      }}>Delete</Button>
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-xs text-white/50">No custom voices uploaded yet.</div>
              )}
            </div>
          </div>
        </Card>

        <Card className="bg-white/5 border-white/10 p-4 space-y-3">
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-cyan-400" />
            <h3 className="text-sm font-medium text-white">Image Generation</h3>
          </div>
          <p className="text-xs text-white/50">Configure the premium image generation feature, provider keys, and safety defaults.</p>

          <div className="grid gap-3">
            <div className="grid sm:grid-cols-2 gap-3">
              <div>
                <Label className="text-xs text-white/70 mb-1 block">Provider</Label>
                <Select value={imageProvider} onValueChange={(value) => setImageProvider(value)}>
                  <SelectTrigger className="bg-white/5 border-white/10 text-white w-full">
                    <SelectValue placeholder="Select provider" />
                  </SelectTrigger>
                  <SelectContent className="bg-gray-900 border-white/20">
                    {availableProviders.length > 0 ? availableProviders.map((item) => (
                      <SelectItem key={item} value={item}>{item.replace('_', ' ').toUpperCase()}</SelectItem>
                    )) : (
                      <>
                        <SelectItem value="huggingface">HuggingFace</SelectItem>
                        <SelectItem value="replicate">Replicate</SelectItem>
                        <SelectItem value="comfyui_local">Local ComfyUI</SelectItem>
                      </>
                    )}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label className="text-xs text-white/70 mb-1 block">Model</Label>
                <Select value={imageModel} onValueChange={(value) => setImageModel(value)}>
                  <SelectTrigger className="bg-white/5 border-white/10 text-white w-full">
                    <SelectValue placeholder="Select model" />
                  </SelectTrigger>
                  <SelectContent className="bg-gray-900 border-white/20">
                    {availableModels.length > 0 ? availableModels.map((item) => (
                      <SelectItem key={item} value={item}>{item}</SelectItem>
                    )) : (
                      <>
                        <SelectItem value="FLUX_DEV">FLUX_DEV</SelectItem>
                        <SelectItem value="FLUX_SCHNELL">FLUX_SCHNELL</SelectItem>
                        <SelectItem value="RELIBERATE_V3">RELIBERATE_V3</SelectItem>
                        <SelectItem value="FLUX_PRO">FLUX_PRO</SelectItem>
                      </>
                    )}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="grid sm:grid-cols-2 gap-3">
              <div>
                <Label className="text-xs text-white/70 mb-1 block">Default Quality</Label>
                <Select value={imageQuality} onValueChange={(value) => setImageQuality(value)}>
                  <SelectTrigger className="bg-white/5 border-white/10 text-white w-full">
                    <SelectValue placeholder="Quality" />
                  </SelectTrigger>
                  <SelectContent className="bg-gray-900 border-white/20">
                    {availableQualities.length > 0 ? availableQualities.map((item) => (
                      <SelectItem key={item} value={item}>{item}</SelectItem>
                    )) : (
                      <>
                        <SelectItem value="DRAFT">Draft</SelectItem>
                        <SelectItem value="STANDARD">Standard</SelectItem>
                        <SelectItem value="HIGH">High</SelectItem>
                      </>
                    )}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label className="text-xs text-white/70 mb-1 block">Local ComfyUI URL</Label>
                <Input
                  value={localComfyUIUrl}
                  onChange={(e) => setLocalComfyUIUrl((e.target as HTMLInputElement).value)}
                  placeholder="http://localhost:8188"
                  className="bg-white/5 border-white/10 text-white"
                />
              </div>
            </div>

            <div className="grid gap-3">
              <div>
                <Label className="text-xs text-white/70 mb-1 block">HuggingFace API Key</Label>
                <Input
                  value={huggingfaceApiKey}
                  onChange={(e) => setHuggingfaceApiKey((e.target as HTMLInputElement).value)}
                  placeholder="Optional API key for HuggingFace"
                  className="bg-white/5 border-white/10 text-white"
                />
              </div>
              <div>
                <Label className="text-xs text-white/70 mb-1 block">Replicate API Key</Label>
                <Input
                  value={replicateApiKey}
                  onChange={(e) => setReplicateApiKey((e.target as HTMLInputElement).value)}
                  placeholder="Optional API key for Replicate"
                  className="bg-white/5 border-white/10 text-white"
                />
              </div>
            </div>

            <div className="grid sm:grid-cols-3 gap-3">
              <Button size="sm" onClick={() => saveImageSettings({ provider: imageProvider, model: imageModel, default_quality: imageQuality, local_comfyui_url: localComfyUIUrl, huggingface_api_key: huggingfaceApiKey, replicate_api_key: replicateApiKey })}>
                Save Image Settings
              </Button>
              <Button size="sm" variant="outline" onClick={() => saveImageSettings({ save_images: !imageSaveImages })}>
                {imageSaveImages ? 'Stop Saving Images' : 'Save Images Automatically'}
              </Button>
              <Button size="sm" variant="outline" onClick={() => saveImageSettings({ sfw_only: !imageSfwOnly })}>
                {imageSfwOnly ? 'SFW Mode On' : 'Allow More Content'}
              </Button>
            </div>

            <div className="grid sm:grid-cols-2 gap-3">
              <Button size="sm" variant={imageAllowSarahGeneration ? undefined : 'outline'} onClick={() => saveImageSettings({ allow_sarah_generation: !imageAllowSarahGeneration })}>
                {imageAllowSarahGeneration ? 'Sarah Image Generation: Enabled' : 'Sarah Image Generation: Disabled'}
              </Button>
              <div className="text-xs text-white/60">
                Sarah-generated images are stored separately and can support vision-aware prompts when Sarah is active.
              </div>
            </div>
          </div>
        </Card>

        <Separator className="bg-white/10" />

        {/* Toggles */}
        <Card className="bg-white/5 border-white/10 p-4 space-y-4">
          <h3 className="text-sm font-medium text-white">Feature Toggles</h3>

          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <MessageCircle className="w-4 h-4 text-green-400" />
              <div>
                <Label className="text-sm text-white">Proactive Chat</Label>
                <p className="text-[10px] text-white/40">Sarah initiates conversation</p>
              </div>
            </div>
            <Switch
              checked={store.proactiveMode}
              onCheckedChange={(v) => {
                store.setProactiveMode(v);
                const ws = getWebSocket();
                if (ws) ws.send(JSON.stringify({ type: 'proactive_mode', enabled: v }));
              }}
            />
          </div>

          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-cyan-400" />
              <div>
                <Label className="text-sm text-white">RP Mode</Label>
                <p className="text-[10px] text-white/40">Enable roleplay rules and persona control</p>
              </div>
            </div>
            <Switch
              checked={store.rpMode}
              onCheckedChange={(v) => {
                store.setRpMode(v);
                const ws = getWebSocket();
                if (ws) ws.send(JSON.stringify({ type: 'config_update', config: { rp_mode: v } }));
              }}
            />
          </div>

          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Brain className="w-4 h-4 text-purple-400" />
              <div>
                <Label className="text-sm text-white">Thinking Mode</Label>
                <p className="text-[10px] text-white/40">Show Sarah's reasoning</p>
              </div>
            </div>
            <Switch
              checked={store.thinkingMode}
              onCheckedChange={(v) => {
                store.setThinkingMode(v);
                const ws = getWebSocket();
                if (ws) ws.send(JSON.stringify({ type: 'thinking_mode', enabled: v }));
              }}
            />
          </div>

          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Eye className="w-4 h-4 text-blue-400" />
              <div>
                <Label className="text-sm text-white">Screen Vision</Label>
                <p className="text-[10px] text-white/40">Sarah can see your screen</p>
              </div>
            </div>
            <Switch
              checked={store.screenVisionEnabled}
              onCheckedChange={(v) => {
                store.setScreenVisionEnabled(v);
                const ws = getWebSocket();
                if (ws) ws.send(JSON.stringify({ type: 'toggle_screen_vision', enabled: v }));
              }}
            />
          </div>

          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Eye className="w-4 h-4 text-indigo-400" />
              <div>
                <Label className="text-sm text-white">Webcam Vision</Label>
                <p className="text-[10px] text-white/40">Sarah can see through webcam</p>
              </div>
            </div>
            <Switch
              checked={store.webcamVisionEnabled}
              onCheckedChange={(v) => {
                store.setWebcamVisionEnabled(v);
                const ws = getWebSocket();
                if (ws) ws.send(JSON.stringify({ type: 'toggle_webcam_vision', enabled: v }));
              }}
            />
          </div>

          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Settings className="w-4 h-4 text-amber-400" />
              <div>
                <Label className="text-sm text-white">Desktop Notifications</Label>
                <p className="text-[10px] text-white/40">Allow Sarah to show notifications when the tab is in background</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Button size="sm" onClick={requestNotificationPermission}>{notificationsEnabled ? 'Enabled' : 'Enable'}</Button>
              <Button size="sm" variant="outline" onClick={enableBackgroundAudio}>Enable Background Audio</Button>
            </div>
          </div>
        </Card>
      </div>
    </ScrollArea>
  );
}
