import { useState, useEffect } from 'react';
import { useStore } from '@/hooks/useStore';
import { useWebSocket } from '@/hooks/useWebSocket';
import VRMViewer from '@/components/VRMViewer';
import ChatPanel from '@/components/ChatPanel';
import SettingsPanel from '@/components/SettingsPanel';
import PermissionPanel from '@/components/PermissionPanel';
import MemoryPanel from '@/components/MemoryPanel';
import OutfitPanel from '@/components/OutfitPanel';
import ImagePanel from '@/components/ImagePanel';
import VRMPanel from '@/components/VRMPanel';
import ChessPanel from '@/components/ChessPanel';
import PetPanel from '@/components/PetPanel';
import EditorPanel from '@/components/EditorPanel';
import ThinkingDisplay from '@/components/ThinkingDisplay';
import StatusBar from '@/components/StatusBar';
import NotesPanel from '@/components/NotesPanel';
import EbooksPanel from '@/components/EbooksPanel';
import { Button } from '@/components/ui/button';
import { 
  MessageSquare, Settings, Shield, Brain, Smile, Swords, Heart, 
  Edit3, Menu, X, Sparkles, Image as ImageIcon, FileText, BookOpen
} from 'lucide-react';

interface Tab {
  id: string;
  label: string;
  icon: React.ReactNode;
  component: React.ComponentType;
}

const tabs: Tab[] = [
  { id: 'chat', label: 'Chat', icon: <MessageSquare className="w-4 h-4" />, component: ChatPanel },
  { id: 'settings', label: 'Settings', icon: <Settings className="w-4 h-4" />, component: SettingsPanel },
  { id: 'permissions', label: 'Permissions', icon: <Shield className="w-4 h-4" />, component: PermissionPanel },
  { id: 'memory', label: 'Memory', icon: <Brain className="w-4 h-4" />, component: MemoryPanel },
  { id: 'notes', label: 'Notes', icon: <FileText className="w-4 h-4" />, component: NotesPanel },
  { id: 'ebooks', label: 'E‑Books', icon: <BookOpen className="w-4 h-4" />, component: EbooksPanel },
  { id: 'images', label: 'Images', icon: <ImageIcon className="w-4 h-4" />, component: ImagePanel },
  { id: 'outfit', label: 'Outfit', icon: <Sparkles className="w-4 h-4" />, component: OutfitPanel },
  { id: 'vrm', label: 'VRM', icon: <Smile className="w-4 h-4" />, component: VRMPanel },
  { id: 'chess', label: 'Chess', icon: <Swords className="w-4 h-4" />, component: ChessPanel },
  { id: 'pet', label: 'Pet', icon: <Heart className="w-4 h-4" />, component: PetPanel },
  { id: 'editor', label: 'Editor', icon: <Edit3 className="w-4 h-4" />, component: EditorPanel },
];

function App() {
  useWebSocket();
  const store = useStore();
  const [panelOpen, setPanelOpen] = useState(true);
  const [activeTab, setActiveTab] = useState('chat');
  const [showWelcome, setShowWelcome] = useState(true);

  useEffect(() => {
    // Fetch initial state
    fetchStatus();
    const interval = setInterval(fetchStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchStatus = async () => {
    try {
      const res = await fetch('/api/status');
      const data = await res.json();
      if (data.permissions) store.setPermissions(data.permissions);
    } catch (e) {}
  };

  useEffect(() => {
    // Auto-dismiss welcome after 4 seconds
    if (showWelcome) {
      const timer = setTimeout(() => setShowWelcome(false), 4000);
      return () => clearTimeout(timer);
    }
  }, [showWelcome]);

  const ActiveComponent = tabs.find(t => t.id === activeTab)?.component || ChatPanel;

  return (
    <div className="w-screen h-screen overflow-hidden bg-[#0a0a12]">
      {/* VRM 3D Background */}
      <VRMViewer />

      {/* Welcome Toast */}
      {showWelcome && (
        <div className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-50 pointer-events-none">
          <div className="bg-black/60 backdrop-blur-xl border border-cyan-500/20 rounded-2xl px-8 py-6 text-center animate-in fade-in zoom-in duration-700">
            <Sparkles className="w-8 h-8 text-cyan-400 mx-auto mb-3 animate-pulse" />
            <h1 className="text-2xl font-bold text-white mb-1">Sarah</h1>
            <p className="text-sm text-cyan-300/70">Your AI Companion is Online</p>
          </div>
        </div>
      )}

      {/* Thinking Display */}
      <ThinkingDisplay />

      {/* Side Panel */}
      <div
        className={`fixed top-0 right-0 h-full z-40 transition-transform duration-300 ease-in-out ${
          panelOpen ? 'translate-x-0' : 'translate-x-full'
        }`}
        style={{ width: '380px', maxWidth: '100vw' }}
      >
        <div className="h-full flex flex-col bg-black/60 backdrop-blur-xl border-l border-white/10">
          {/* Panel Header */}
          <div className="flex items-center justify-between px-4 py-3 border-b border-white/10">
            <div className="flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-cyan-400" />
              <span className="text-sm font-semibold text-white">Sarah AI</span>
            </div>
            <Button
              onClick={() => setPanelOpen(false)}
              variant="ghost"
              size="icon"
              className="h-7 w-7 text-white/40 hover:text-white hover:bg-white/10"
            >
              <X className="w-4 h-4" />
            </Button>
          </div>

          {/* Tab Navigation */}
          <div className="flex gap-0.5 p-1.5 bg-white/5 border-b border-white/5 overflow-x-auto">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-1 px-2.5 py-1.5 rounded-md text-[11px] font-medium whitespace-nowrap transition-all ${
                  activeTab === tab.id
                    ? 'bg-cyan-500/20 text-cyan-300'
                    : 'text-white/40 hover:text-white/70 hover:bg-white/5'
                }`}
              >
                {tab.icon}
                {tab.label}
              </button>
            ))}
          </div>

          {/* Panel Content */}
          <div className="flex-1 overflow-hidden">
            <ActiveComponent />
          </div>

          {/* Status Bar */}
          <StatusBar />
        </div>
      </div>

      {/* Toggle Button (when panel is closed) */}
      {!panelOpen && (
        <Button
          onClick={() => setPanelOpen(true)}
          className="fixed top-4 right-4 z-40 bg-black/50 backdrop-blur-md border border-white/10 hover:bg-white/10 text-white"
          size="sm"
        >
          <Menu className="w-4 h-4 mr-1" />
          Open Panel
        </Button>
      )}

      {/* Sarah Status Overlay (bottom left) */}
      <div className="fixed bottom-4 left-4 z-30 pointer-events-none">
        <div className="bg-black/40 backdrop-blur-sm border border-white/10 rounded-lg px-3 py-2">
          <div className="flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${store.isConnected ? 'bg-emerald-400' : 'bg-red-400'}`} />
            <span className="text-xs text-white/60">Sarah</span>
            <span className="text-[10px] text-white/40 capitalize">{store.sarahStatus}</span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
