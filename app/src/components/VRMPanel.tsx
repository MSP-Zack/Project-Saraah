import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Smile, Frown, Angry, Zap, Heart, Moon, Sun, Eye, Hand, Footprints, PartyPopper, RotateCcw, Bed, Music, CircleDot } from 'lucide-react';

const expressions = [
  { name: 'happy', icon: <Smile className="w-4 h-4" />, label: 'Happy', color: 'text-yellow-400' },
  { name: 'sad', icon: <Frown className="w-4 h-4" />, label: 'Sad', color: 'text-blue-400' },
  { name: 'angry', icon: <Angry className="w-4 h-4" />, label: 'Angry', color: 'text-red-400' },
  { name: 'surprised', icon: <Zap className="w-4 h-4" />, label: 'Surprised', color: 'text-purple-400' },
  { name: 'relaxed', icon: <Sun className="w-4 h-4" />, label: 'Relaxed', color: 'text-green-400' },
  { name: 'blink', icon: <Eye className="w-4 h-4" />, label: 'Blink', color: 'text-cyan-400' },
];

const animations = [
  { name: 'wave', icon: <Hand className="w-4 h-4" />, label: 'Wave', color: 'text-pink-400' },
  { name: 'kiss', icon: <Heart className="w-4 h-4" />, label: 'Kiss', color: 'text-rose-400' },
  { name: 'hug', icon: <Heart className="w-4 h-4" />, label: 'Hug', color: 'text-red-400' },
  { name: 'punch', icon: <Zap className="w-4 h-4" />, label: 'Punch', color: 'text-orange-400' },
  { name: 'kick', icon: <Footprints className="w-4 h-4" />, label: 'Kick', color: 'text-yellow-400' },
  { name: 'dance', icon: <Music className="w-4 h-4" />, label: 'Dance', color: 'text-purple-400' },
  { name: 'jump', icon: <PartyPopper className="w-4 h-4" />, label: 'Jump', color: 'text-green-400' },
  { name: 'bow', icon: <CircleDot className="w-4 h-4" />, label: 'Bow', color: 'text-indigo-400' },
  { name: 'clap', icon: <Hand className="w-4 h-4" />, label: 'Clap', color: 'text-cyan-400' },
  { name: 'spin', icon: <RotateCcw className="w-4 h-4" />, label: 'Spin', color: 'text-teal-400' },
  { name: 'nod', icon: <CircleDot className="w-4 h-4" />, label: 'Nod', color: 'text-lime-400' },
  { name: 'shake_head', icon: <CircleDot className="w-4 h-4" />, label: 'Shake No', color: 'text-amber-400' },
  { name: 'sit', icon: <Bed className="w-4 h-4" />, label: 'Sit', color: 'text-sky-400' },
  { name: 'sleep', icon: <Moon className="w-4 h-4" />, label: 'Sleep', color: 'text-violet-400' },
];

export default function VRMPanel() {
  const triggerExpression = (name: string) => {
    window.dispatchEvent(new CustomEvent('vrm-expression', { detail: name }));
  };

  const triggerAnimation = (name: string) => {
    window.dispatchEvent(new CustomEvent('vrm-animation', { detail: name }));
  };

  return (
    <ScrollArea className="h-full px-4 py-4">
      <div className="space-y-4">
        <div className="flex items-center gap-2 mb-2">
          <Smile className="w-5 h-5 text-pink-400" />
          <h2 className="text-lg font-semibold text-white">VRM Controls</h2>
        </div>
        <p className="text-xs text-white/40">Manually trigger expressions and animations</p>

        {/* Expressions */}
        <Card className="bg-white/5 border-white/10 p-3">
          <h3 className="text-xs font-semibold text-white/60 uppercase tracking-wider mb-2">Expressions</h3>
          <div className="grid grid-cols-3 gap-1.5">
            {expressions.map((expr) => (
              <Button
                key={expr.name}
                variant="ghost"
                size="sm"
                onClick={() => triggerExpression(expr.name)}
                className={`justify-start gap-1.5 text-xs h-8 hover:bg-white/10 ${expr.color}`}
              >
                {expr.icon}
                {expr.label}
              </Button>
            ))}
          </div>
        </Card>

        {/* Animations */}
        <Card className="bg-white/5 border-white/10 p-3">
          <h3 className="text-xs font-semibold text-white/60 uppercase tracking-wider mb-2">Animations</h3>
          <div className="grid grid-cols-2 gap-1.5">
            {animations.map((anim) => (
              <Button
                key={anim.name}
                variant="ghost"
                size="sm"
                onClick={() => triggerAnimation(anim.name)}
                className={`justify-start gap-1.5 text-xs h-8 hover:bg-white/10 ${anim.color}`}
              >
                {anim.icon}
                {anim.label}
              </Button>
            ))}
          </div>
        </Card>

        {/* Body Interactions Info */}
        <Card className="bg-white/5 border-white/10 p-3">
          <h3 className="text-xs font-semibold text-white/60 uppercase tracking-wider mb-2">Body Interactions</h3>
          <p className="text-xs text-white/40 mb-2">Click on Sarah's body parts:</p>
          <div className="space-y-1">
            {[
              { part: 'Head', reaction: 'Pats, happy reaction' },
              { part: 'Face/Cheek', reaction: 'Blushes, shy reaction' },
              { part: 'Hand', reaction: 'Holds your hand' },
              { part: 'Chest', reaction: 'Surprised, teasing' },
              { part: 'Shoulder', reaction: 'Leans in, comforted' },
              { part: 'Stomach', reaction: 'Giggles, ticklish' },
              { part: 'Leg', reaction: 'Shy, nervous' },
              { part: 'Hair', reaction: 'Content, loves it' },
            ].map((item) => (
              <div key={item.part} className="flex items-center gap-2 text-xs">
                <span className="text-cyan-400 w-20 shrink-0">{item.part}</span>
                <span className="text-white/40">{item.reaction}</span>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </ScrollArea>
  );
}
