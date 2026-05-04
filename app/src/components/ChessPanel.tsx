import { useEffect, useState } from 'react';
import { useStore } from '@/hooks/useStore';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { RotateCcw, Swords } from 'lucide-react';

const pieceSymbols: Record<string, string> = {
  'K': '\u2654', 'Q': '\u2655', 'R': '\u2656', 'B': '\u2657', 'N': '\u2658', 'P': '\u2659',
  'k': '\u265A', 'q': '\u265B', 'r': '\u265C', 'b': '\u265D', 'n': '\u265E', 'p': '\u265F',
  '.': ''
};

const pieceColors: Record<string, string> = {
  'K': 'text-amber-200', 'Q': 'text-amber-200', 'R': 'text-amber-200', 'B': 'text-amber-200', 'N': 'text-amber-200', 'P': 'text-amber-200',
  'k': 'text-slate-400', 'q': 'text-slate-400', 'r': 'text-slate-400', 'b': 'text-slate-400', 'n': 'text-slate-400', 'p': 'text-slate-400',
};

export default function ChessPanel() {
  const store = useStore();
  const [board, setBoard] = useState<string[][]>([
    ['r','n','b','q','k','b','n','r'],
    ['p','p','p','p','p','p','p','p'],
    ['.','.','.','.','.','.','.','.'],
    ['.','.','.','.','.','.','.','.'],
    ['.','.','.','.','.','.','.','.'],
    ['.','.','.','.','.','.','.','.'],
    ['P','P','P','P','P','P','P','P'],
    ['R','N','B','Q','K','B','N','R']
  ]);
  const [selected, setSelected] = useState<{row: number, col: number} | null>(null);
  const [validMoves, setValidMoves] = useState<{row: number, col: number}[]>([]);
  const [gameOver, setGameOver] = useState(false);
  const [winner, setWinner] = useState<string | null>(null);
  const [currentPlayer, setCurrentPlayer] = useState('white');

  useEffect(() => {
    if (store.chessBoard) {
      setBoard(store.chessBoard.board);
      setCurrentPlayer(store.chessBoard.current_player);
      setGameOver(store.chessBoard.game_over);
      setWinner(store.chessBoard.winner);
      if (store.chessBoard.valid_moves) {
        // Store valid moves
      }
    }
  }, [store.chessBoard]);

  const startNewGame = async () => {
    try {
      const res = await fetch('/api/chess/new', { method: 'POST' });
      const data = await res.json();
      if (data.board) {
        setBoard(data.board);
        setCurrentPlayer(data.current_player);
        setGameOver(data.game_over);
        setWinner(data.winner);
        setSelected(null);
        setValidMoves([]);
        store.setChessBoard(data);
      }
    } catch (e) {
      console.error('Failed to start chess game:', e);
    }
  };

  const handleCellClick = async (row: number, col: number) => {
    if (gameOver) return;
    if (currentPlayer !== 'white') return; // Only user plays white

    const piece = board[row][col];

    if (selected) {
      // Try to move
      try {
        const res = await fetch(`/api/chess/move?from_row=${selected.row}&from_col=${selected.col}&to_row=${row}&to_col=${col}`, {
          method: 'POST'
        });
        const data = await res.json();
        
        if (data.player_move?.success) {
          setBoard(data.board.board);
          setCurrentPlayer(data.board.current_player);
          setGameOver(data.board.game_over);
          setWinner(data.board.winner);
          setSelected(null);
          setValidMoves([]);
          store.setChessBoard(data.board);

          // Check for AI move
          if (data.ai_move?.success && !data.board.game_over) {
            setTimeout(() => {
              setBoard(data.ai_move.board.board);
              setCurrentPlayer(data.ai_move.board.current_player);
              setGameOver(data.ai_move.board.game_over);
              setWinner(data.ai_move.board.winner);
              store.setChessBoard(data.ai_move.board);
            }, 500);
          }
        } else {
          // Invalid move, try selecting new piece
          if (piece !== '.' && piece === piece.toUpperCase()) {
            setSelected({ row, col });
            highlightMoves(row, col);
          } else {
            setSelected(null);
            setValidMoves([]);
          }
        }
      } catch (e) {
        console.error('Move failed:', e);
      }
    } else if (piece !== '.' && piece === piece.toUpperCase()) {
      // Select piece
      setSelected({ row, col });
      highlightMoves(row, col);
    }
  };

  const highlightMoves = async (row: number, col: number) => {
    try {
      const res = await fetch('/api/chess/board');
      const data = await res.json();
      if (data.valid_moves) {
        const moves = data.valid_moves
          .filter((m: any) => m.from.row === row && m.from.col === col)
          .map((m: any) => ({ row: m.to.row, col: m.to.col }));
        setValidMoves(moves);
      }
    } catch (e) {}
  };

  const isValidMove = (row: number, col: number) => {
    return validMoves.some(m => m.row === row && m.col === col);
  };

  return (
    <div className="h-full flex flex-col px-4 py-4">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Swords className="w-5 h-5 text-amber-400" />
          <h2 className="text-lg font-semibold text-white">Chess</h2>
        </div>
        <Button onClick={startNewGame} size="sm" className="bg-amber-500/20 hover:bg-amber-500/30 text-amber-300 border border-amber-500/30">
          <RotateCcw className="w-3 h-3 mr-1" /> New Game
        </Button>
      </div>

      {gameOver && (
        <div className="mb-2 p-2 rounded-lg bg-amber-500/10 border border-amber-500/20 text-center">
          <p className="text-sm font-medium text-amber-300">
            {winner ? `${winner === 'white' ? 'You' : 'Sarah'} wins!` : 'Draw!'}
          </p>
        </div>
      )}

      <div className="flex items-center gap-2 mb-2">
        <Badge variant="outline" className={`text-xs ${currentPlayer === 'white' ? 'border-amber-400 text-amber-300' : 'border-slate-400 text-slate-300'}`}>
          {currentPlayer === 'white' ? 'Your Turn' : "Sarah's Turn"}
        </Badge>
      </div>

      {/* Board */}
      <div className="flex-1 flex items-center justify-center">
        <div className="grid grid-cols-8 gap-0 border-2 border-amber-700/50 rounded overflow-hidden" style={{ maxWidth: '320px', maxHeight: '320px' }}>
          {board.map((row, ri) =>
            row.map((cell, ci) => {
              const isDark = (ri + ci) % 2 === 1;
              const isSelected = selected?.row === ri && selected?.col === ci;
              const isValid = isValidMove(ri, ci);
              return (
                <div
                  key={`${ri}-${ci}`}
                  onClick={() => handleCellClick(ri, ci)}
                  className={`
                    w-9 h-9 flex items-center justify-center cursor-pointer text-lg select-none transition-all
                    ${isDark ? 'bg-amber-900/60' : 'bg-amber-100/10'}
                    ${isSelected ? 'ring-2 ring-cyan-400 z-10' : ''}
                    ${isValid ? 'ring-1 ring-green-400/50' : ''}
                    hover:brightness-125
                  `}
                >
                  {cell !== '.' && (
                    <span className={`${pieceColors[cell]} text-lg leading-none`}>
                      {pieceSymbols[cell]}
                    </span>
                  )}
                  {isValid && cell === '.' && (
                    <div className="w-2 h-2 rounded-full bg-green-400/40" />
                  )}
                  {isValid && cell !== '.' && (
                    <div className="absolute w-9 h-9 rounded-full border-2 border-green-400/40" />
                  )}
                </div>
              );
            })
          )}
        </div>
      </div>

      {/* Captured pieces */}
      {store.chessBoard && (
        <div className="mt-2 space-y-1">
          {store.chessBoard.captured_black.length > 0 && (
            <div className="flex items-center gap-1 text-xs">
              <span className="text-white/40">Captured:</span>
              {store.chessBoard.captured_black.map((p, i) => (
                <span key={i} className="text-amber-200">{pieceSymbols[p]}</span>
              ))}
            </div>
          )}
        </div>
      )}

      <p className="text-[10px] text-white/30 mt-2 text-center">You play White, Sarah plays Black</p>
    </div>
  );
}
