import { useEffect, useState } from 'react';
import { useStore } from '@/hooks/useStore';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Heart, Utensils, Bath, Gamepad2, Moon, Sun, Pill, Power } from 'lucide-react';

export default function PetPanel() {
  const store = useStore();
  const [petEnabled, setPetEnabled] = useState(false);
  const [settingLoaded, setSettingLoaded] = useState(false);
  const [settingBusy, setSettingBusy] = useState(false);
  const [settingError, setSettingError] = useState('');

  useEffect(() => {
    fetch('/api/pet/enabled')
      .then((res) => res.json())
      .then((data) => {
        const enabled = Boolean(data.enabled);
        setPetEnabled(enabled);
        if (enabled) fetchPetState();
      })
      .catch(() => setSettingError('Could not load the pet setting.'))
      .finally(() => setSettingLoaded(true));
  }, []);

  const fetchPetState = async () => {
    try {
      const res = await fetch('/api/pet/state');
      const data = await res.json();
      store.setPetState(data);
    } catch (e) {}
  };

  const sendPetAction = (action: string, foodType?: string) => {
    // Use one transport per action. Sending both the websocket event and HTTP
    // fallback applied every care action twice and duplicated activity writes.
    fetch(`/api/pet/${action}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ type: foodType }),
    }).then(() => fetchPetState());
  };

  const togglePet = async () => {
    setSettingBusy(true);
    setSettingError('');
    try {
      const res = await fetch('/api/pet/enabled', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ enabled: !petEnabled }),
      });
      const data = await res.json();
      if (!res.ok || typeof data.enabled !== 'boolean') throw new Error('Could not change pet setting.');
      setPetEnabled(data.enabled);
      if (data.enabled) fetchPetState();
    } catch (error) {
      setSettingError(error instanceof Error ? error.message : 'Could not change pet setting.');
    } finally {
      setSettingBusy(false);
    }
  };

  const pet = store.petState;

  if (!settingLoaded) {
    return <div className="h-full flex items-center justify-center text-sm text-white/50">Loading pet setting...</div>;
  }

  if (!petEnabled) {
    return (
      <div className="h-full flex flex-col items-center justify-center px-6 text-center">
        <Heart className="w-10 h-10 text-pink-400/40 mb-3" />
        <h2 className="text-base font-semibold text-white">Pet demo is off</h2>
        <p className="mt-2 max-w-xs text-xs leading-relaxed text-white/50">
          The pet runs separately from Sarah and never uses Gemini. Turn it on only when you want to try the demo.
        </p>
        <Button onClick={togglePet} disabled={settingBusy} className="mt-4 bg-blue-600 hover:bg-blue-500">
          <Power className="mr-2 h-4 w-4" /> Turn pet on
        </Button>
        {settingError && <p className="mt-3 text-xs text-red-300">{settingError}</p>}
      </div>
    );
  }

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
        <div className="flex items-center justify-between gap-2">
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <Heart className="w-5 h-5 shrink-0 text-pink-400" />
              <h2 className="truncate text-lg font-semibold text-white">{pet.name}</h2>
            </div>
            <p className="ml-7 mt-0.5 text-[10px] text-white/40">Standalone demo · no Gemini calls</p>
          </div>
          <div className="flex shrink-0 items-center gap-2">
            <Badge variant="outline" className="text-xs border-pink-500/30 text-pink-300 capitalize">
              {pet.species} - {pet.stage}
            </Badge>
            <Button onClick={togglePet} disabled={settingBusy} size="sm" variant="outline" className="h-7 px-2 text-[10px]">
              <Power className="mr-1 h-3 w-3" /> Off
            </Button>
          </div>
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
