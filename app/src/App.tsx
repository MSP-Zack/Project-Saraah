import { useState, useEffect, useRef } from 'react';
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
import StrategoPanel from '@/components/StrategoPanel';
import PetPanel from '@/components/PetPanel';
import EditorPanel from '@/components/EditorPanel';
import ThinkingDisplay from '@/components/ThinkingDisplay';
import StatusBar from '@/components/StatusBar';
import NotesPanel from '@/components/NotesPanel';
import EbooksPanel from '@/components/EbooksPanel';
import ToolsPanel from '@/components/ToolsPanel';
import VRMActionsPanel from '@/components/VRMActionsPanel';
import DiaryPanel from '@/components/DiaryPanel';
import PerceptionPanel from '@/components/PerceptionPanel';
import FBXTestPanel from '@/components/FBXTestPanel';
import SelfModelPanel from '@/components/SelfModelPanel';
import GoalsPanel from '@/components/GoalsPanel';
import HeartbeatPanel from '@/components/HeartbeatPanel';
import { Button } from '@/components/ui/button';
import { 
  MessageSquare, Settings, Shield, Brain, Smile, Swords, Heart, Target, UserRound, Activity,
  Edit3, Menu, X, Sparkles, Image as ImageIcon, FileText, BookOpen, Eye, Box
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
  { id: 'diary', label: 'Diary', icon: <Eye className="w-4 h-4" />, component: DiaryPanel },
  { id: 'perception', label: 'Perception', icon: <Eye className="w-4 h-4" />, component: PerceptionPanel },
  { id: 'fbx_tests', label: 'FBX Tests', icon: <Box className="w-4 h-4" />, component: FBXTestPanel },
  { id: 'self_model', label: 'Self', icon: <UserRound className="w-4 h-4" />, component: SelfModelPanel },
  { id: 'goals', label: 'Goals', icon: <Target className="w-4 h-4" />, component: GoalsPanel },
  { id: 'heartbeat', label: 'Heartbeat', icon: <Activity className="w-4 h-4" />, component: HeartbeatPanel },
  { id: 'notes', label: 'Notes', icon: <FileText className="w-4 h-4" />, component: NotesPanel },
  { id: 'tools', label: 'Tools', icon: <Sparkles className="w-4 h-4" />, component: ToolsPanel },
  { id: 'vrm_actions', label: 'VRM', icon: <Smile className="w-4 h-4" />, component: VRMActionsPanel },
  { id: 'ebooks', label: 'E‑Books', icon: <BookOpen className="w-4 h-4" />, component: EbooksPanel },
  { id: 'images', label: 'Images', icon: <ImageIcon className="w-4 h-4" />, component: ImagePanel },
  { id: 'outfit', label: 'Outfit', icon: <Sparkles className="w-4 h-4" />, component: OutfitPanel },
  { id: 'vrm', label: 'VRM', icon: <Smile className="w-4 h-4" />, component: VRMPanel },
  { id: 'chess', label: 'Chess', icon: <Swords className="w-4 h-4" />, component: ChessPanel },
  { id: 'stratego', label: 'Stratego', icon: <Shield className="w-4 h-4" />, component: StrategoPanel },
  { id: 'pet', label: 'Pet', icon: <Heart className="w-4 h-4" />, component: PetPanel },
  { id: 'editor', label: 'Editor', icon: <Edit3 className="w-4 h-4" />, component: EditorPanel },
];

function App() {
  useWebSocket();
  const store = useStore();
  const [panelOpen, setPanelOpen] = useState(true);
  const [activeTab, setActiveTab] = useState('chat');
  const [showWelcome, setShowWelcome] = useState(true);
  const tabNavRef = useRef<HTMLElement>(null);
  const [tabScroll, setTabScroll] = useState({ left: 0, max: 0 });

  useEffect(() => {
    // Fetch initial state
    fetchStatus();
    const interval = setInterval(fetchStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const nav = tabNavRef.current;
    if (!nav) return;

    const updateScrollRange = () => {
      const max = Math.max(0, nav.scrollWidth - nav.clientWidth);
      setTabScroll({ left: Math.min(nav.scrollLeft, max), max });
    };

    updateScrollRange();
    nav.addEventListener('scroll', updateScrollRange, { passive: true });
    const resizeObserver = new ResizeObserver(updateScrollRange);
    resizeObserver.observe(nav);
    return () => {
      nav.removeEventListener('scroll', updateScrollRange);
      resizeObserver.disconnect();
    };
  }, []);

  const fetchStatus = async () => {
    try {
      const res = await fetch('/api/status');
      const data = await res.json();
      const permissionResponse = await fetch('/api/permissions');
      if (permissionResponse.ok) store.setPermissions(await permissionResponse.json());
      if (data.capabilities) store.setSttEnabled(Boolean(data.capabilities.stt));
      if (data.runtime) {
        store.setScreenVisionEnabled(Boolean(data.runtime.screen_vision_enabled));
        store.setWebcamVisionEnabled(Boolean(data.runtime.webcam_vision_enabled));
        store.setWebcamVisionDescription(data.runtime.latest_webcam_vision_description || '');
        store.setWebcamVisionTimestamp(data.runtime.webcam_vision_last_updated || '');
      }
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

      {/* Live webcam vision overlay */}
      {store.webcamVisionEnabled && store.webcamVisionDescription && (
        <div className="fixed top-[116px] left-4 right-[420px] z-40 pointer-events-none">
          <div className="rounded-3xl border border-violet-400/20 bg-black/70 p-3 text-xs text-slate-100 shadow-2xl shadow-violet-500/5 backdrop-blur-md">
            <div className="flex items-start justify-between gap-3">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="inline-flex h-2.5 w-2.5 rounded-full bg-violet-400 animate-pulse" />
                  <span className="text-[10px] uppercase tracking-[0.22em] text-violet-300">Live camera vision</span>
                </div>
                <p className="text-sm leading-snug text-white">{store.webcamVisionDescription}</p>
              </div>
              {store.webcamVisionTimestamp && (
                <span className="text-[10px] text-white/40">{new Date(store.webcamVisionTimestamp).toLocaleTimeString()}</span>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Full-width title and navigation */}
      <header className="fixed inset-x-0 top-0 z-50 border-b border-white/10 bg-[#080811]/85 shadow-lg shadow-black/20 backdrop-blur-xl">
        <div className="relative flex h-16 items-center justify-center border-b border-white/5">
          <div className="pointer-events-none absolute inset-0 bg-gradient-to-r from-cyan-500/10 via-violet-500/10 to-pink-500/10" />
          <div className="relative flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl border border-cyan-300/25 bg-cyan-400/10 shadow-lg shadow-cyan-500/10">
              <Sparkles className="h-5 w-5 text-cyan-200" />
            </div>
            <div className="text-center">
              <h1 className="bg-gradient-to-r from-cyan-200 via-white to-violet-200 bg-clip-text text-xl font-semibold tracking-[0.16em] text-transparent">Sarah AI</h1>
              <p className="text-[9px] uppercase tracking-[0.32em] text-cyan-100/45">Companion</p>
            </div>
          </div>
          <Button
            onClick={() => setPanelOpen(!panelOpen)}
            variant="ghost"
            size="icon"
            className="absolute right-3 top-1/2 h-9 w-9 -translate-y-1/2 text-white/55 hover:bg-white/10 hover:text-white"
            aria-label={panelOpen ? 'Hide Sarah panel' : 'Show Sarah panel'}
            title={panelOpen ? 'Hide panel' : 'Show panel'}
          >
            {panelOpen ? <X className="h-4 w-4" /> : <Menu className="h-4 w-4" />}
          </Button>
        </div>
        <div className="relative h-10">
        <nav ref={tabNavRef} aria-label="Sarah sections" className="sarah-tab-strip flex h-10 items-center gap-1 px-2">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              type="button"
              role="tab"
              aria-selected={activeTab === tab.id}
              onClick={() => {
                setActiveTab(tab.id);
                setPanelOpen(true);
              }}
              className={`flex h-7 shrink-0 items-center gap-1 rounded-lg px-2 text-[11px] font-medium whitespace-nowrap transition-colors ${
                activeTab === tab.id
                  ? 'border border-blue-400/30 bg-blue-500/20 text-blue-100 shadow-sm shadow-blue-950/40'
                  : 'border border-transparent text-white/55 hover:bg-white/8 hover:text-white/90'
              }`}
            >
              {tab.icon}
              {tab.label}
            </button>
          ))}
        </nav>
        {tabScroll.max > 0 && (
          <input
            type="range"
            aria-label="Scroll navigation tabs horizontally"
            min={0}
            max={tabScroll.max}
            value={Math.min(tabScroll.left, tabScroll.max)}
            onChange={(event) => {
              const left = Number(event.target.value);
              if (tabNavRef.current) tabNavRef.current.scrollLeft = left;
              setTabScroll((current) => ({ ...current, left }));
            }}
            className="sarah-tab-range absolute inset-x-3 bottom-0 z-10 h-2 w-auto cursor-pointer"
          />
        )}
        </div>
      </header>

      {/* Feature content stays docked on the right, below the global navigation. */}
      <aside
        className={`fixed right-0 z-40 transition-transform duration-300 ease-in-out ${
          panelOpen ? 'translate-x-0' : 'translate-x-full'
        }`}
        style={{ width: '380px', maxWidth: '100vw', top: '104px', height: 'calc(100vh - 104px)' }}
      >
        <div className="flex h-full min-h-0 flex-col border-l border-white/10 bg-black/60 shadow-2xl shadow-black/20 backdrop-blur-xl">
          <div className="min-h-0 flex-1 overflow-hidden">
            <ActiveComponent />
          </div>
          <StatusBar />
        </div>
      </aside>

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
