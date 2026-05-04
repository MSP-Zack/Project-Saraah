import { useEffect } from 'react';
import { useStore } from '@/hooks/useStore';
import { getWebSocket } from '@/hooks/useWebSocket';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Heart, Utensils, Bath, Gamepad2, Moon, Sun, Pill } from 'lucide-react';

export default function PetPanel() {
  const store = useStore();

  useEffect(() => {
    fetchPetState();
    const interval = setInterval(fetchPetState, 10000);
    return () => clearInterval(interval);
  }, []);

  const fetchPetState = async () => {
    try {
      const res = await fetch('/api/pet/state');
      const data = await res.json();
      store.setPetState(data);
    } catch (e) {}
  };

  const sendPetAction = (action: string, foodType?: string) => {
    const ws = getWebSocket();
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: 'pet_action', action, action_type: foodType }));
    }
    // Also update via HTTP as fallback
    fetch(`/api/pet/${action}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ type: foodType }),
    }).then(() => fetchPetState());
  };

  const pet = store.petState;

  if (!pet) {
    return (
      <div className="h-full flex flex-col items-center justify-center px-4">
        <Heart className="w-10 h-10 text-pink-400/30 mb-3" />
        <p className="text-sm text-white/40">Loading pet...</p>
      </div>
    );
  }

  const statBar = (value: number, color: string) => (
    <div className="w-full bg-white/10 rounded-full h-2 overflow-hidden">
      <div
        className={`h-full rounded-full transition-all ${color}`}
        style={{ width: `${value}%` }}
      />
    </div>
  );

  const moodEmojis: Record<string, string> = {
    happy: '\uD83D\uDE0A', sad: '\uD83D\uDE22', excited: '\uD83E\uDD73', tired: '\uD83D\uDE34',
    sick: '\uD83E\uDD22', hungry: '\uD83E\uDD24', angry: '\uD83D\uDE20', grumpy: '\uD83D\uDE3C',
    sleeping: '\uD83D\uDCA4'
  };

  return (
    <ScrollArea className="h-full px-4 py-4">
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Heart className="w-5 h-5 text-pink-400" />
            <h2 className="text-lg font-semibold text-white">{pet.name}</h2>
          </div>
          <Badge variant="outline" className="text-xs border-pink-500/30 text-pink-300 capitalize">
            {pet.species} - {pet.stage}
          </Badge>
        </div>

        {/* Status */}
        <div className="flex items-center gap-2">
          <span className="text-2xl">{moodEmojis[pet.mood] || '\u2728'}</span>
          <div>
            <p className="text-sm font-medium text-white capitalize">{pet.mood}</p>
            <p className="text-[10px] text-white/40">
              {pet.is_sleeping ? 'Sleeping' : pet.is_sick ? 'Sick - needs medicine' : 'Active'}
            </p>
          </div>
        </div>

        {/* Stats */}
        <Card className="bg-white/5 border-white/10 p-3 space-y-2.5">
          <div>
            <div className="flex justify-between text-xs mb-1">
              <span className="text-white/60">Hunger</span>
              <span className="text-orange-400">{Math.round(pet.hunger)}%</span>
            </div>
            {statBar(pet.hunger, 'bg-gradient-to-r from-orange-600 to-orange-400')}
          </div>
          <div>
            <div className="flex justify-between text-xs mb-1">
              <span className="text-white/60">Energy</span>
              <span className="text-blue-400">{Math.round(pet.energy)}%</span>
            </div>
            {statBar(pet.energy, 'bg-gradient-to-r from-blue-600 to-blue-400')}
          </div>
          <div>
            <div className="flex justify-between text-xs mb-1">
              <span className="text-white/60">Happiness</span>
              <span className="text-pink-400">{Math.round(pet.happiness)}%</span>
            </div>
            {statBar(pet.happiness, 'bg-gradient-to-r from-pink-600 to-pink-400')}
          </div>
          <div>
            <div className="flex justify-between text-xs mb-1">
              <span className="text-white/60">Hygiene</span>
              <span className="text-cyan-400">{Math.round(pet.hygiene)}%</span>
            </div>
            {statBar(pet.hygiene, 'bg-gradient-to-r from-cyan-600 to-cyan-400')}
          </div>
          <div>
            <div className="flex justify-between text-xs mb-1">
              <span className="text-white/60">Health</span>
              <span className="text-green-400">{Math.round(pet.health)}%</span>
            </div>
            {statBar(pet.health, 'bg-gradient-to-r from-green-600 to-green-400')}
          </div>
        </Card>

        {/* Actions */}
        <div className="grid grid-cols-3 gap-1.5">
          <Button onClick={() => sendPetAction('feed')} size="sm" className="bg-orange-500/20 hover:bg-orange-500/30 text-orange-300 border border-orange-500/30 text-xs h-9">
            <Utensils className="w-3 h-3 mr-1" /> Feed
          </Button>
          <Button onClick={() => sendPetAction('pet')} size="sm" className="bg-pink-500/20 hover:bg-pink-500/30 text-pink-300 border border-pink-500/30 text-xs h-9">
            <Heart className="w-3 h-3 mr-1" /> Pet
          </Button>
          <Button onClick={() => sendPetAction('play')} size="sm" className="bg-purple-500/20 hover:bg-purple-500/30 text-purple-300 border border-purple-500/30 text-xs h-9">
            <Gamepad2 className="w-3 h-3 mr-1" /> Play
          </Button>
          <Button onClick={() => sendPetAction('clean')} size="sm" className="bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-300 border border-cyan-500/30 text-xs h-9">
            <Bath className="w-3 h-3 mr-1" /> Clean
          </Button>
          {pet.is_sleeping ? (
            <Button onClick={() => sendPetAction('wake_up')} size="sm" className="bg-yellow-500/20 hover:bg-yellow-500/30 text-yellow-300 border border-yellow-500/30 text-xs h-9">
              <Sun className="w-3 h-3 mr-1" /> Wake
            </Button>
          ) : (
            <Button onClick={() => sendPetAction('sleep')} size="sm" className="bg-indigo-500/20 hover:bg-indigo-500/30 text-indigo-300 border border-indigo-500/30 text-xs h-9">
              <Moon className="w-3 h-3 mr-1" /> Sleep
            </Button>
          )}
          <Button onClick={() => sendPetAction('medicate')} size="sm" className="bg-green-500/20 hover:bg-green-500/30 text-green-300 border border-green-500/30 text-xs h-9">
            <Pill className="w-3 h-3 mr-1" /> Meds
          </Button>
        </div>

        {/* Recent Messages */}
        {pet.recent_messages && pet.recent_messages.length > 0 && (
          <Card className="bg-white/5 border-white/10 p-3">
            <h3 className="text-xs font-semibold text-white/60 mb-2">Recent Activity</h3>
            <div className="space-y-1 max-h-[120px] overflow-y-auto">
              {pet.recent_messages.slice(0, 5).map((msg: any, i: number) => (
                <p key={i} className="text-xs text-white/50">{msg.text}</p>
              ))}
            </div>
          </Card>
        )}
      </div>
    </ScrollArea>
  );
}
