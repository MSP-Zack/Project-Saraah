import { useRef, useEffect } from 'react';
import { useStore } from '@/hooks/useStore';
import { getWebSocket } from '@/hooks/useWebSocket';
import { Send, Mic, MicOff, Volume2, VolumeX, Brain } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';

export default function ChatPanel() {
  const store = useStore();
  const scrollRef = useRef<HTMLDivElement>(null);
  const recognitionRef = useRef<any>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [store.messages]);

  // Browser STT setup
  useEffect(() => {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (SpeechRecognition && store.sttEnabled) {
      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = false;
      recognition.lang = 'en-US';

      recognition.onresult = (event: any) => {
        const transcript = event.results[0][0].transcript;
        sendMessage(transcript);
        store.setIsRecording(false);
      };

      recognition.onerror = () => {
        store.setIsRecording(false);
      };

      recognition.onend = () => {
        store.setIsRecording(false);
      };

      recognitionRef.current = recognition;
    }
  }, [store.sttEnabled]);

  const sendMessage = (text: string) => {
    if (!text.trim()) return;

    const ws = getWebSocket();
    if (ws && ws.readyState === WebSocket.OPEN) {
      // Add user message
      store.addMessage({
        id: Date.now().toString(),
        role: 'user',
        content: text,
        timestamp: new Date().toISOString(),
      });

      ws.send(JSON.stringify({
        type: 'text',
        content: text,
        tts_enabled: store.ttsEnabled,
        use_vision: store.webcamVisionEnabled,
      }));

      store.setInputText('');
      store.setSarahStatus('thinking');
    }
  };

  const toggleRecording = () => {
    if (store.isRecording) {
      recognitionRef.current?.stop();
      store.setIsRecording(false);
    } else {
      recognitionRef.current?.start();
      store.setIsRecording(true);
    }
  };

  const formatTime = (iso: string) => {
    try {
      return new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } catch {
      return '';
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage(store.inputText);
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Messages */}
      <ScrollArea className="flex-1 px-4 py-2" ref={scrollRef}>
        <div className="space-y-3">
          {store.messages.length === 0 && (
            <div className="text-center text-white/30 py-12">
              <p className="text-sm">Say hello to Sarah!</p>
              <p className="text-xs mt-1">She's excited to meet you~</p>
            </div>
          )}
          {store.messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}
            >
              {msg.thinking && store.thinkingMode && (
                <div className="max-w-[85%] mb-1 px-3 py-1.5 rounded-lg bg-yellow-500/10 border border-yellow-500/20">
                  <div className="flex items-center gap-1 mb-0.5">
                    <Brain className="w-3 h-3 text-yellow-400" />
                    <span className="text-[10px] font-medium text-yellow-400 uppercase tracking-wider">Thinking</span>
                  </div>
                  <p className="text-xs text-yellow-200/70 leading-relaxed italic">{msg.thinking}</p>
                </div>
              )}
              <div
                className={`max-w-[85%] px-3 py-2 rounded-2xl ${
                  msg.role === 'user'
                    ? 'bg-gradient-to-br from-rose-500/20 to-pink-600/10 border border-rose-500/30 text-white'
                    : msg.isProactive
                    ? 'bg-gradient-to-br from-cyan-500/10 to-blue-600/5 border border-cyan-500/20 text-gray-100'
                    : 'bg-white/5 border border-white/10 text-gray-200'
                }`}
              >
                <p className="text-sm leading-relaxed whitespace-pre-wrap">{msg.content}</p>
                {msg.actions && msg.actions.length > 0 && (
                  <div className="flex gap-1 mt-1.5 flex-wrap">
                    {msg.actions.map((a, i) => (
                      <Badge key={i} variant="outline" className="text-[9px] h-4 border-white/20 text-white/50">
                        {a.type}: {a.name}
                      </Badge>
                    ))}
                  </div>
                )}
                <p className="text-[10px] text-white/30 mt-1 text-right">{formatTime(msg.timestamp)}</p>
              </div>
            </div>
          ))}
          {store.sarahStatus === 'thinking' && (
            <div className="flex items-start gap-2">
              <div className="bg-white/5 border border-white/10 rounded-2xl px-4 py-3">
                <div className="flex gap-1">
                  <div className="w-2 h-2 rounded-full bg-cyan-400 animate-bounce" style={{ animationDelay: '0ms' }} />
                  <div className="w-2 h-2 rounded-full bg-cyan-400 animate-bounce" style={{ animationDelay: '150ms' }} />
                  <div className="w-2 h-2 rounded-full bg-cyan-400 animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
              </div>
            </div>
          )}
        </div>
      </ScrollArea>

      {/* Input */}
      <div className="p-3 border-t border-white/10 bg-black/20 backdrop-blur-md">
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="icon"
            className={`shrink-0 rounded-full transition-all ${
              store.isRecording ? 'bg-red-500/20 text-red-400 animate-pulse' : 'text-white/40 hover:text-white hover:bg-white/10'
            }`}
            onClick={toggleRecording}
            disabled={!store.sttEnabled}
            title={store.sttEnabled ? 'Voice input' : 'STT disabled'}
          >
            {store.isRecording ? <Mic className="w-4 h-4" /> : <MicOff className="w-4 h-4" />}
          </Button>

          <Input
            value={store.inputText}
            onChange={(e) => store.setInputText(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type a message to Sarah..."
            className="flex-1 bg-white/5 border-white/10 text-white placeholder:text-white/30 focus:border-cyan-500/50 h-9"
          />

          <Button
            variant="ghost"
            size="icon"
            className="shrink-0 rounded-full text-white/40 hover:text-white hover:bg-white/10"
            onClick={() => store.setTtsEnabled(!store.ttsEnabled)}
            title="Toggle TTS"
          >
            {store.ttsEnabled ? <Volume2 className="w-4 h-4" /> : <VolumeX className="w-4 h-4" />}
          </Button>

          <Button
            size="icon"
            className="shrink-0 rounded-full bg-gradient-to-r from-cyan-500 to-blue-500 hover:from-cyan-400 hover:to-blue-400 h-9 w-9"
            onClick={() => sendMessage(store.inputText)}
            disabled={!store.inputText.trim()}
          >
            <Send className="w-4 h-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}
