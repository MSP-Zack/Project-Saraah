import { create } from 'zustand';
import type { AppState, ChatMessage, ChessBoardState, StrategoBoardState, PetState, PermissionMap, EditorDocument } from '@/types';

interface StoreState extends AppState {
  // Actions
  setConnected: (connected: boolean) => void;
  setSarahStatus: (status: string) => void;
  addMessage: (msg: ChatMessage) => void;
  setInputText: (text: string) => void;
  setIsRecording: (recording: boolean) => void;
  setTtsEnabled: (enabled: boolean) => void;
  setSttEnabled: (enabled: boolean) => void;
  setScreenVisionEnabled: (enabled: boolean) => void;
  setWebcamVisionEnabled: (enabled: boolean) => void;
  setWebcamVisionDescription: (description: string) => void;
  setWebcamVisionTimestamp: (timestamp: string) => void;
  setThinkingMode: (enabled: boolean) => void;
  setProactiveMode: (enabled: boolean) => void;
  setRpMode: (enabled: boolean) => void;
  setActiveTab: (tab: string) => void;
  setSystemPrompt: (prompt: string) => void;
  setVoiceProfile: (profile: string) => void;
  setPermissions: (perms: PermissionMap) => void;
  setCurrentThinking: (thinking: string) => void;
  setChessBoard: (board: ChessBoardState | null) => void;
  setSelectedChessPiece: (piece: { row: number; col: number } | null) => void;
  setStrategoBoard: (board: StrategoBoardState | null) => void;
  setSelectedStrategoPiece: (piece: { row: number; col: number } | null) => void;
  setPetState: (state: PetState | null) => void;
  setDocuments: (docs: { id: string; title: string; modified: string; preview: string }[]) => void;
  setActiveDocument: (doc: EditorDocument | null) => void;
  setEditorContent: (content: string) => void;
  setCurrentOutfit: (outfit: string) => void;
  setAvailableOutfits: (outfits: any[]) => void;
  clearMessages: () => void;
}

export const useStore = create<StoreState>((set) => ({
  // Initial state
  isConnected: false,
  sarahStatus: 'idle',
  messages: [],
  inputText: '',
  isRecording: false,
  ttsEnabled: true,
  sttEnabled: true,
  screenVisionEnabled: false,
  webcamVisionEnabled: false,
  webcamVisionDescription: '',
  webcamVisionTimestamp: '',
  thinkingMode: false,
  proactiveMode: true,
  rpMode: false,
  activeTab: 'chat',
  systemPrompt: '',
  voiceProfile: 'default',
  permissions: {},
  vrmState: {
    currentVrm: null,
    expression: 'neutral',
    animation: 'idle',
    isTalking: false,
    blinkState: false,
    lipSyncValue: 0,
  },
  outfitState: {
    currentOutfit: 'default',
    availableOutfits: [],
    isTransitioning: false,
    transitionProgress: 0,
  },
  currentThinking: '',
  chessBoard: null,
  selectedChessPiece: null,
  strategoBoard: null,
  selectedStrategoPiece: null,
  petState: null,
  documents: [],
  activeDocument: null,
  editorContent: '',

  // Actions
  setConnected: (connected) => set({ isConnected: connected }),
  setSarahStatus: (status) => set({ sarahStatus: status }),
  addMessage: (msg) => set((state) => ({ messages: [...state.messages, msg] })),
  setInputText: (text) => set({ inputText: text }),
  setIsRecording: (recording) => set({ isRecording: recording }),
  setTtsEnabled: (enabled) => set({ ttsEnabled: enabled }),
  setSttEnabled: (enabled) => set({ sttEnabled: enabled }),
  setScreenVisionEnabled: (enabled) => set({ screenVisionEnabled: enabled }),
  setWebcamVisionEnabled: (enabled) => set({ webcamVisionEnabled: enabled }),
  setWebcamVisionDescription: (description) => set({ webcamVisionDescription: description }),
  setWebcamVisionTimestamp: (timestamp) => set({ webcamVisionTimestamp: timestamp }),
  setThinkingMode: (enabled) => set({ thinkingMode: enabled }),
  setProactiveMode: (enabled) => set({ proactiveMode: enabled }),
  setRpMode: (enabled) => set({ rpMode: enabled }),
  setActiveTab: (tab) => set({ activeTab: tab }),
  setSystemPrompt: (prompt) => set({ systemPrompt: prompt }),
  setVoiceProfile: (profile) => set({ voiceProfile: profile }),
  setPermissions: (perms) => set({ permissions: perms }),
  setCurrentThinking: (thinking) => set({ currentThinking: thinking }),
  setChessBoard: (board) => set({ chessBoard: board }),
  setSelectedChessPiece: (piece) => set({ selectedChessPiece: piece }),
  setStrategoBoard: (board) => set({ strategoBoard: board }),
  setSelectedStrategoPiece: (piece) => set({ selectedStrategoPiece: piece }),
  setPetState: (state) => set({ petState: state }),
  setDocuments: (docs) => set({ documents: docs }),
  setActiveDocument: (doc) => set({ activeDocument: doc }),
  setEditorContent: (content) => set({ editorContent: content }),
  setCurrentOutfit: (outfit) => set((state) => ({
    outfitState: { ...state.outfitState, currentOutfit: outfit }
  })),
  setAvailableOutfits: (outfits) => set((state) => ({
    outfitState: { ...state.outfitState, availableOutfits: outfits }
  })),
  clearMessages: () => set({ messages: [] }),
}));
