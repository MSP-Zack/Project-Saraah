import { useStore } from '@/hooks/useStore';
import { Badge } from '@/components/ui/badge';
import { Wifi, WifiOff, Mic, MicOff, Volume2, VolumeX, Eye, Brain } from 'lucide-react';

export default function StatusBar() {
  const store = useStore();

  const statusColors: Record<string, string> = {
    idle: 'text-emerald-400',
    thinking: 'text-yellow-400 animate-pulse',
    offline: 'text-red-400',
    listening: 'text-cyan-400 animate-pulse',
    speaking: 'text-pink-400 animate-pulse',
  };

  return (
    <div className="flex items-center justify-between px-3 py-1.5 bg-black/40 backdrop-blur-sm border-t border-white/5">
      <div className="flex items-center gap-3">
        {/* Connection */}
        <div className="flex items-center gap-1">
          {store.isConnected ? (
            <Wifi className="w-3 h-3 text-emerald-400" />
          ) : (
            <WifiOff className="w-3 h-3 text-red-400" />
          )}
          <span className={`text-[10px] ${store.isConnected ? 'text-emerald-400' : 'text-red-400'}`}>
            {store.isConnected ? 'Online' : 'Offline'}
          </span>
        </div>

        {/* Sarah Status */}
        <div className="flex items-center gap-1">
          <div className={`w-1.5 h-1.5 rounded-full ${statusColors[store.sarahStatus] || 'text-white/40'}`} />
          <span className={`text-[10px] capitalize ${statusColors[store.sarahStatus] || 'text-white/40'}`}>
            {store.sarahStatus}
          </span>
        </div>
      </div>

      <div className="flex items-center gap-2">
        {/* Feature indicators */}
        {store.ttsEnabled ? (
          <Volume2 className="w-3 h-3 text-pink-400/60" />
        ) : (
          <VolumeX className="w-3 h-3 text-white/20" />
        )}

        {store.sttEnabled ? (
          <Mic className="w-3 h-3 text-cyan-400/60" />
        ) : (
          <MicOff className="w-3 h-3 text-white/20" />
        )}

        {store.screenVisionEnabled && (
          <Eye className="w-3 h-3 text-blue-400/60" />
        )}

        {store.webcamVisionEnabled && (
          <Eye className="w-3 h-3 text-indigo-400/60" />
        )}

        {store.thinkingMode && (
          <Brain className="w-3 h-3 text-yellow-400/60" />
        )}

        {/* Message count */}
        <Badge variant="outline" className="text-[9px] h-4 border-white/10 text-white/30">
          {store.messages.length} msgs
        </Badge>
      </div>
    </div>
  );
}
