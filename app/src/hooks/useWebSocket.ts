import { useEffect, useRef, useCallback } from 'react';
import { useStore } from './useStore';
import type { ChatMessage, ChessBoardState, PetState, StrategoBoardState } from '@/types';

let ws: WebSocket | null = null;
let messageHandlers: ((msg: any) => void)[] = [];

export function getWebSocket(): WebSocket | null {
  return ws;
}

export function useWebSocket() {
  const store = useStore();
  const wsRef = useRef<WebSocket | null>(null);

  const connect = useCallback(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws`;
    
    ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('[WS]: Connected to Sarah');
      (window as any).sarahWS = ws;
      store.setConnected(true);
      store.setSarahStatus('idle');
    };

    ws.onclose = () => {
      console.log('[WS]: Disconnected');
      (window as any).sarahWS = null;
      store.setConnected(false);
      store.setSarahStatus('offline');
      // Auto reconnect
      setTimeout(connect, 3000);
    };

    ws.onerror = (err) => {
      console.error('[WS]: Error:', err);
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        handleMessage(data);
        messageHandlers.forEach((h) => h(data));
      } catch (e) {
        console.error('[WS]: Parse error:', e);
      }
    };
  }, []);

  const handleMessage = (data: any) => {
    if (data.action === 'reply') {
      const msg: ChatMessage = {
        id: Date.now().toString(),
        role: 'assistant',
        content: data.text || '',
        timestamp: data.timestamp || new Date().toISOString(),
        actions: data.actions || [],
        thinking: data.thinking || '',
        isProactive: data.is_proactive || false,
      };
      store.addMessage(msg);
      
      if (data.thinking) {
        store.setCurrentThinking(data.thinking);
      }

      // Trigger VRM speaking animation and lip-sync when Sarah replies.
      if (data.text) {
        window.dispatchEvent(new CustomEvent('vrm-lipsync', { detail: 1 }));
      }

      // Play audio if available
      if (data.audio_url) {
        const audio = new Audio(data.audio_url + '?t=' + Date.now());
        audio.play().catch(() => {});
      }

      // Handle VRM actions
      if (data.actions && data.actions.length > 0) {
        data.actions.forEach((action: any) => {
          if (action.type === 'expression') {
            // Trigger expression via event
            window.dispatchEvent(new CustomEvent('vrm-expression', { detail: action.name }));
          } else if (action.type === 'animation') {
            window.dispatchEvent(new CustomEvent('vrm-animation', { detail: action.name }));
          }
        });
      }
    } else if (data.action === 'system') {
      store.setSarahStatus(data.text || 'idle');
    } else if (data.action === 'screen_capture') {
      window.dispatchEvent(new CustomEvent('screen-capture', { detail: data.image }));
    } else if (data.action === 'vrm_reaction') {
      if (data.expression) {
        window.dispatchEvent(new CustomEvent('vrm-expression', { detail: data.expression }));
      }
      if (data.animation) {
        window.dispatchEvent(new CustomEvent('vrm-animation', { detail: data.animation }));
      }
    } else if (data.action === 'interrupt_tts') {
      // Stop any ongoing audio playback
      const audioElements = document.querySelectorAll('audio');
      audioElements.forEach(audio => audio.pause());
      console.log('[WS]: TTS interrupted');
    } else if (data.action === 'chess_update') {
      if (data.result?.board) {
        store.setChessBoard(data.result.board as ChessBoardState);
      } else if (data.result?.player_move?.board) {
        store.setChessBoard(data.result.player_move.board as ChessBoardState);
      }
    } else if (data.action === 'stratego_update') {
      if (data.result?.board) {
        store.setStrategoBoard(data.result.board as StrategoBoardState);
      } else if (data.result?.player_move?.board) {
        store.setStrategoBoard(data.result.player_move.board as StrategoBoardState);
      }
    } else if (data.action === 'pet_update') {
      if (data.result?.state) {
        store.setPetState(data.result.state as PetState);
      }
    } else if (data.action === 'pet_move') {
      // Forward movement instruction to the VRM viewer via DOM event
      try {
        window.dispatchEvent(new CustomEvent('pet-move', { detail: data.detail }));
      } catch (e) {
        console.warn('pet_move event dispatch failed', e);
      }
    } else if (data.action === 'editor_update') {
      if (data.result?.document) {
        store.setActiveDocument(data.result.document);
        store.setEditorContent(data.result.document.content);
      }
    } else if (data.action === 'tool_result') {
      // Show tool result in chat
      if (data.result) {
        const msg: ChatMessage = {
          id: Date.now().toString() + '_tool',
          role: 'assistant',
          content: `Tool \`${data.result.tool}\`: ${data.result.success ? 'Success' : 'Failed'} - ${JSON.stringify(data.result.output || data.result.error || '')}`,
          timestamp: new Date().toISOString(),
        };
        store.addMessage(msg);
      }
    }
  };

  const sendMessage = useCallback((type: string, data: any = {}) => {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type, ...data }));
    }
  }, []);

  useEffect(() => {
    connect();
    return () => {
      if (ws) {
        ws.close();
        ws = null;
      }
    };
  }, [connect]);

  return { sendMessage, connect };
}

export function onWebSocketMessage(handler: (msg: any) => void) {
  messageHandlers.push(handler);
  return () => {
    messageHandlers = messageHandlers.filter((h) => h !== handler);
  };
}
