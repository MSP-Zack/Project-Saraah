import { useStore } from '@/hooks/useStore';
import { Card } from '@/components/ui/card';
import { Brain, X } from 'lucide-react';
import { Button } from '@/components/ui/button';

export default function ThinkingDisplay() {
  const store = useStore();

  if (!store.thinkingMode || !store.currentThinking) return null;

  return (
    <Card className="fixed bottom-24 left-1/2 -translate-x-1/2 z-50 bg-black/80 border-yellow-500/30 backdrop-blur-md max-w-lg w-[90%]">
      <div className="p-3">
        <div className="flex items-center justify-between mb-1.5">
          <div className="flex items-center gap-1.5">
            <Brain className="w-3.5 h-3.5 text-yellow-400" />
            <span className="text-[10px] font-semibold text-yellow-400 uppercase tracking-wider">Sarah's Thoughts</span>
          </div>
          <Button
            onClick={() => store.setCurrentThinking('')}
            size="sm"
            variant="ghost"
            className="h-5 w-5 p-0 text-white/40 hover:text-white"
          >
            <X className="w-3 h-3" />
          </Button>
        </div>
        <p className="text-xs text-yellow-100/70 leading-relaxed italic">
          {store.currentThinking}
        </p>
      </div>
    </Card>
  );
}
