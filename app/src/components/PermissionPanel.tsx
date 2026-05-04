import { useStore } from '@/hooks/useStore';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Shield, AlertTriangle, Mouse, Keyboard, FileText, Globe, AppWindow, Monitor, Camera, MessageSquare, User, Terminal } from 'lucide-react';
import { useEffect, useState } from 'react';

const iconMap: Record<string, React.ReactNode> = {
  mouse: <Mouse className="w-4 h-4" />,
  keyboard: <Keyboard className="w-4 h-4" />,
  file: <FileText className="w-4 h-4" />,
  browser: <Globe className="w-4 h-4" />,
  app: <AppWindow className="w-4 h-4" />,
  screen: <Monitor className="w-4 h-4" />,
  camera: <Camera className="w-4 h-4" />,
  chat: <MessageSquare className="w-4 h-4" />,
  user: <User className="w-4 h-4" />,
  terminal: <Terminal className="w-4 h-4" />,
};

const riskColors: Record<string, string> = {
  low: 'bg-green-500/20 text-green-400 border-green-500/30',
  medium: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
  high: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
  critical: 'bg-red-500/20 text-red-400 border-red-500/30',
};

export default function PermissionPanel() {
  const store = useStore();
  const [permissions, setPermissions] = useState<Record<string, any>>({});

  useEffect(() => {
    fetchPermissions();
  }, []);

  const fetchPermissions = async () => {
    try {
      const res = await fetch('/api/permissions');
      const data = await res.json();
      setPermissions(data);
      store.setPermissions(data);
    } catch (e) {
      console.error('Failed to fetch permissions:', e);
    }
  };

  const togglePermission = async (key: string, enabled: boolean) => {
    try {
      const res = await fetch('/api/permissions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ key, enabled }),
      });
      const data = await res.json();
      if (data.success) {
        setPermissions(data.permissions);
        store.setPermissions(data.permissions);
      }
    } catch (e) {
      console.error('Failed to update permission:', e);
    }
  };

  const categories = [
    { name: 'Input Control', keys: ['mouse_control', 'keyboard_control'] },
    { name: 'System Access', keys: ['file_operations', 'app_control', 'system_shell'] },
    { name: 'Network', keys: ['browser_control'] },
    { name: 'Vision', keys: ['screen_vision', 'webcam_vision'] },
    { name: 'Sarah Features', keys: ['proactive_chat', 'vrm_actions', 'memory_edit'] },
  ];

  return (
    <ScrollArea className="h-full px-4 py-4">
      <div className="space-y-4">
        <div className="flex items-center gap-2 mb-2">
          <Shield className="w-5 h-5 text-emerald-400" />
          <h2 className="text-lg font-semibold text-white">Permissions</h2>
        </div>
        <p className="text-xs text-white/40 mb-4">Control what Sarah is allowed to do on your system</p>

        {categories.map((cat) => (
          <Card key={cat.name} className="bg-white/5 border-white/10 p-3 space-y-2">
            <h3 className="text-xs font-semibold text-white/60 uppercase tracking-wider">{cat.name}</h3>
            <Separator className="bg-white/5" />
            {cat.keys.map((key) => {
              const perm = permissions[key];
              if (!perm) return null;
              return (
                <div key={key} className="flex items-center justify-between py-1.5">
                  <div className="flex items-center gap-2.5">
                    <div className="text-white/40">{iconMap[perm.icon] || <Shield className="w-4 h-4" />}</div>
                    <div>
                      <div className="flex items-center gap-2">
                        <Label className="text-sm text-white capitalize">{key.replace(/_/g, ' ')}</Label>
                        <Badge variant="outline" className={`text-[9px] h-4 ${riskColors[perm.risk] || ''}`}>
                          {perm.risk}
                        </Badge>
                      </div>
                      <p className="text-[10px] text-white/40">{perm.description}</p>
                    </div>
                  </div>
                  <Switch
                    checked={perm.enabled}
                    onCheckedChange={(v) => togglePermission(key, v)}
                  />
                </div>
              );
            })}
          </Card>
        ))}

        {Object.values(permissions).some((p: any) => p.risk === 'critical' && p.enabled) && (
          <div className="flex items-center gap-2 p-3 rounded-lg bg-red-500/10 border border-red-500/20">
            <AlertTriangle className="w-4 h-4 text-red-400 shrink-0" />
            <p className="text-xs text-red-300">
              Critical permissions are enabled. Sarah can perform high-risk actions on your system.
            </p>
          </div>
        )}
      </div>
    </ScrollArea>
  );
}
