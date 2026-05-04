export interface VRMState {
  currentVrm: any | null;
  expression: string;
  animation: string;
  isTalking: boolean;
  blinkState: boolean;
  lipSyncValue: number;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  actions?: VRMAction[];
  thinking?: string;
  isProactive?: boolean;
}

export interface VRMAction {
  type: 'animation' | 'expression';
  name: string;
}

export interface Permission {
  enabled: boolean;
  description: string;
  risk: string;
  icon: string;
}

export interface PermissionMap {
  [key: string]: Permission;
}

export interface MemoryEntry {
  id: number;
  title: string;
  content: string;
  importance: number;
  timestamp: string;
}

export interface ConversationEntry {
  id: number;
  role: string;
  content: string;
  timestamp: string;
  metadata?: Record<string, any>;
}

export interface ChessMove {
  from: { row: number; col: number };
  to: { row: number; col: number };
  piece: string;
  captured?: string;
}

export interface ChessBoardState {
  board: string[][];
  current_player: string;
  move_history: string[];
  captured_white: string[];
  captured_black: string[];
  game_over: boolean;
  winner: string | null;
  is_draw: boolean;
  valid_moves: ChessMove[];
}

export interface PetState {
  name: string;
  species: string;
  stage: string;
  hunger: number;
  energy: number;
  happiness: number;
  hygiene: number;
  health: number;
  mood: string;
  is_sleeping: boolean;
  is_sick: boolean;
  recent_messages: { text: string; time: string }[];
}

export interface EditorDocument {
  id: string;
  title: string;
  content: string;
  modified: string;
  suggestions: EditorSuggestion[];
  user_cursor: number;
  sarah_cursor: number;
  is_sarah_typing: boolean;
}

export interface EditorSuggestion {
  id: number;
  text: string;
  explanation: string;
  timestamp: string;
  accepted: boolean | null;
}

export interface OutfitState {
  currentOutfit: string;
  availableOutfits: any[];
  isTransitioning: boolean;
  transitionProgress: number;
}

export interface AppState {
  // Connection
  isConnected: boolean;
  sarahStatus: string;
  
  // Chat
  messages: ChatMessage[];
  inputText: string;
  isRecording: boolean;
  
  // Features
  ttsEnabled: boolean;
  sttEnabled: boolean;
  screenVisionEnabled: boolean;
  webcamVisionEnabled: boolean;
  thinkingMode: boolean;
  proactiveMode: boolean;
  rpMode: boolean;
  
  // Current tab
  activeTab: string;
  
  // Settings
  systemPrompt: string;
  voiceProfile: string;
  
  // Permissions
  permissions: PermissionMap;
  
  // VRM
  vrmState: VRMState;
  
  // Outfit
  outfitState: OutfitState;
  
  // Thinking
  currentThinking: string;
  
  // Games
  chessBoard: ChessBoardState | null;
  selectedChessPiece: { row: number; col: number } | null;
  
  // Pet
  petState: PetState | null;
  
  // Editor
  documents: { id: string; title: string; modified: string; preview: string }[];
  activeDocument: EditorDocument | null;
  editorContent: string;
}

export type TabId = 
  | 'chat' 
  | 'settings' 
  | 'permissions' 
  | 'memory' 
  | 'vrm' 
  | 'chess' 
  | 'pet' 
  | 'editor'
  | 'thinking';
