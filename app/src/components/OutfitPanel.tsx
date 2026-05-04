import { useEffect, useState } from 'react';
import { useStore } from '@/hooks/useStore';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import { Loader2, Check, Sparkles } from 'lucide-react';

interface Outfit {
  id: string;
  name: string;
  description: string;
  path: string;
  thumbnail?: string;
  color_scheme: string;
}

export default function OutfitPanel() {
  const [outfits, setOutfits] = useState<Record<string, Outfit>>({});
  const [loading, setLoading] = useState(true);
  const [switching, setSwitching] = useState(false);
  const [currentOutfit, setCurrentOutfit] = useState('default');
  const store = useStore();

  // Fetch available outfits
  useEffect(() => {
    const fetchOutfits = async () => {
      try {
        const response = await fetch('/api/vrm/models');
        const data = await response.json();
        setOutfits(data.models);
        setCurrentOutfit(data.current);
        store.setAvailableOutfits(Object.values(data.models));
      } catch (error) {
        console.error('Failed to fetch outfits:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchOutfits();
  }, []);

  const switchOutfit = async (outfitId: string) => {
    if (outfitId === currentOutfit || switching) return;

    setSwitching(true);
    try {
      const response = await fetch('/api/vrm/outfit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ outfit_id: outfitId })
      });

      const data = await response.json();
      if (data.success) {
        setCurrentOutfit(outfitId);
        store.setCurrentOutfit(outfitId);
        // Trigger VRM model change animation
        window.dispatchEvent(new CustomEvent('vrm-outfit-change', {
          detail: { outfitId, outfitData: data.outfit_data }
        }));
      }
    } catch (error) {
      console.error('Failed to switch outfit:', error);
    } finally {
      setSwitching(false);
    }
  };

  const colorSchemeClasses: Record<string, string> = {
    pink_purple: 'from-pink-500 to-purple-500',
    neon_blue: 'from-cyan-500 to-blue-600',
    warm_tones: 'from-orange-400 to-red-400',
    gold_white: 'from-yellow-400 to-white',
    purple_stars: 'from-violet-600 to-indigo-600'
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin mx-auto mb-2 text-pink-400" />
          <p className="text-sm text-white/60">Loading outfits...</p>
        </div>
      </div>
    );
  }

  return (
    <ScrollArea className="h-full px-4 py-4">
      <div className="space-y-4">
        <div className="flex items-center gap-2 mb-2">
          <Sparkles className="w-5 h-5 text-pink-400" />
          <h2 className="text-lg font-semibold text-white">Outfits</h2>
        </div>
        <p className="text-xs text-white/40">Switch Sarah's avatar outfit with smooth animation</p>

        {/* Available Outfits Grid */}
        <div className="grid grid-cols-1 gap-3">
          {Object.entries(outfits).map(([key, outfit]) => (
            <Card
              key={key}
              className={`bg-white/5 border-white/10 overflow-hidden cursor-pointer transition-all duration-300 hover:border-pink-400/50 ${
                currentOutfit === key ? 'ring-2 ring-pink-400 border-pink-400' : ''
              }`}
              onClick={() => switchOutfit(key)}
            >
              <div className="p-3 space-y-2">
                {/* Outfit Header */}
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                      {outfit.name}
                      {currentOutfit === key && (
                        <Check className="w-4 h-4 text-pink-400" />
                      )}
                    </h3>
                    <p className="text-xs text-white/50">{outfit.description}</p>
                  </div>

                  {/* Color Scheme Indicator */}
                  <div
                    className={`w-8 h-8 rounded-full bg-gradient-to-br ${
                      colorSchemeClasses[outfit.color_scheme]
                    } opacity-80 flex-shrink-0`}
                  />
                </div>

                {/* Preview Image or Placeholder */}
                {outfit.thumbnail ? (
                  <div className="relative w-full h-32 rounded-lg overflow-hidden bg-black/40 flex items-center justify-center">
                    <img
                      src={outfit.thumbnail}
                      alt={outfit.name}
                      className="w-full h-full object-cover"
                      onError={(e) => {
                        (e.target as HTMLImageElement).style.display = 'none';
                      }}
                    />
                  </div>
                ) : (
                  <div className="w-full h-32 rounded-lg bg-gradient-to-br from-white/10 to-white/5 flex items-center justify-center border border-white/10">
                    <Sparkles className="w-6 h-6 text-white/30" />
                  </div>
                )}

                {/* Action Button */}
                <Button
                  className={`w-full h-8 text-xs ${
                    currentOutfit === key
                      ? 'bg-pink-500/20 hover:bg-pink-500/30 border border-pink-400/50 text-pink-300'
                      : 'bg-white/10 hover:bg-white/20 border border-white/10 text-white'
                  }`}
                  disabled={switching || currentOutfit === key}
                  onClick={() => switchOutfit(key)}
                >
                  {switching && currentOutfit !== key ? (
                    <>
                      <Loader2 className="w-3 h-3 animate-spin mr-1" />
                      Switching...
                    </>
                  ) : currentOutfit === key ? (
                    <>
                      <Check className="w-3 h-3 mr-1" />
                      Current
                    </>
                  ) : (
                    'Switch'
                  )}
                </Button>

                {/* Color Scheme Badge */}
                <Badge className="w-fit bg-white/10 text-white/70 border-white/20 text-xs">
                  {outfit.color_scheme.replace(/_/g, ' ')}
                </Badge>
              </div>
            </Card>
          ))}
        </div>

        {/* Info */}
        <Card className="bg-white/5 border-white/10 p-3">
          <h3 className="text-xs font-semibold text-white/60 uppercase tracking-wider mb-2">
            Outfit Switching
          </h3>
          <ul className="space-y-1 text-xs text-white/40">
            <li>• Select an outfit to see Sarah transform</li>
            <li>• Changes apply with smooth fade animation</li>
            <li>• Your preference is saved automatically</li>
            <li>• All animations continue during transition</li>
          </ul>
        </Card>
      </div>
    </ScrollArea>
  );
}