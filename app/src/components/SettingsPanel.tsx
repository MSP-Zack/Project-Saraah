import { useStore } from '@/hooks/useStore';
import { getWebSocket } from '@/hooks/useWebSocket';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Textarea } from '@/components/ui/textarea';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Card } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import { Settings, Brain, MessageCircle, Volume2, Eye, Sparkles } from 'lucide-react';

export default function SettingsPanel() {
  const store = useStore();

  const sendConfig = (updates: any) => {
    const ws = getWebSocket();
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: 'config_update', ...updates }));
    }
  };

  const handleSystemPromptChange = (value: string) => {
    store.setSystemPrompt(value);
  };

  const handleSavePrompt = () => {
    sendConfig({ system_prompt: store.systemPrompt });
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
            <SelectTrigger className="bg-white/5 border-white/10 text-white">
              <SelectValue placeholder="Select voice" />
            </SelectTrigger>
            <SelectContent className="bg-gray-900 border-white/20">
              <SelectItem value="default">Sarah Cute (Default)</SelectItem>
              <SelectItem value="excited">Excited</SelectItem>
              <SelectItem value="shy">Shy</SelectItem>
              <SelectItem value="tsundere">Tsundere</SelectItem>
              <SelectItem value="gentle">Gentle</SelectItem>
            </SelectContent>
          </Select>
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
        </Card>
      </div>
    </ScrollArea>
  );
}
