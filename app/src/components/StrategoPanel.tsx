import { useEffect, useMemo, useState } from 'react';
import { useStore } from '@/hooks/useStore';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { RotateCcw, Shield, HelpCircle } from 'lucide-react';

const pieceLabels: Record<string, string> = {
  N: '10',
  G: '9',
  C: '8',
  M: '7',
  A: '6',
  L: '5',
  E: '4',
  R: '3',
  O: '2',
  P: '1',
  S: 'Spy',
  F: 'Flag',
  B: 'Bomb',
};

const pieceNames: Record<string, string> = {
  N: 'Marshal',
  G: 'General',
  C: 'Colonel',
  M: 'Major',
  A: 'Captain',
  L: 'Lieutenant',
  E: 'Sergeant',
  R: 'Miner',
  O: 'Scout',
  P: 'Private',
  S: 'Spy',
  F: 'Flag',
  B: 'Bomb',
};

const presetOptions = [
  { value: 'classic', label: 'Classic 10×10' },
  { value: 'open', label: 'Open field 10×10' },
  { value: 'custom', label: 'Custom board' },
];

const difficultyLabels: Record<number, string> = {
  1: 'Easy',
  2: 'Casual',
  3: 'Normal',
  4: 'Hard',
  5: 'Very Hard',
  6: 'Impossible',
};

const pieceOrder = ['N', 'G', 'C', 'M', 'A', 'L', 'E', 'R', 'O', 'P', 'S', 'B', 'F'];

const defaultCustomPieceCounts: Record<string, number> = {
  N: 1,
  G: 1,
  C: 2,
  M: 3,
  A: 4,
  L: 4,
  E: 4,
  R: 5,
  O: 8,
  P: 10,
  S: 1,
  B: 6,
  F: 1,
};

const getCode = (cell: string) => (cell === '.' ? '.' : cell.slice(1));
const isOwnCell = (cell: string) => cell.startsWith('w');
const createEmptyBoard = (rows = 10, cols = 10) => Array.from({ length: rows }, () => Array(cols).fill('.'));

export default function StrategoPanel() {
  const store = useStore();
  const [board, setBoard] = useState<string[][]>(createEmptyBoard());
  const [selected, setSelected] = useState<{ row: number; col: number } | null>(null);
  const [validMoves, setValidMoves] = useState<{ row: number; col: number }[]>([]);
  const [currentPlayer, setCurrentPlayer] = useState('white');
  const [gameOver, setGameOver] = useState(false);
  const [winner, setWinner] = useState<string | null>(null);
  const [difficulty, setDifficulty] = useState(3);
  const [preset, setPreset] = useState('classic');
  const [customRows, setCustomRows] = useState(10);
  const [customColumns, setCustomColumns] = useState(10);
  const [customPieceCounts, setCustomPieceCounts] = useState<Record<string, number>>(defaultCustomPieceCounts);
  const [boardConfig, setBoardConfig] = useState<{ preset: string; rows: number; columns: number; initial_rows: number; obstacles: [number, number][]; piece_counts: Record<string, number>; } | null>(null);
  const [showRules, setShowRules] = useState(false);
  const [pieceCounts, setPieceCounts] = useState<Record<string, number>>({});
  const [deploymentCounts, setDeploymentCounts] = useState<Record<string, number>>(defaultCustomPieceCounts);
  const [selectedSetupPiece, setSelectedSetupPiece] = useState<string>('N');
  const [setupPhase, setSetupPhase] = useState(false);
  const [saveMessage, setSaveMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [capturedWhite, setCapturedWhite] = useState<string[]>([]);

  const updateStateFromResponse = (newState: any) => {
    store.setStrategoBoard(newState);
    setBoard(newState.board || createEmptyBoard());
    setCurrentPlayer(newState.current_player || 'white');
    setGameOver(newState.game_over || false);
    setWinner(newState.winner || null);
    const counts = newState.piece_counts?.white;
    setPieceCounts(typeof counts === 'object' && counts !== null ? (counts as Record<string, number>) : {});
    setDeploymentCounts(newState.deployment_counts || (typeof counts === 'object' && counts !== null ? (counts as Record<string, number>) : {}));
    setSetupPhase(newState.setup_phase || false);
    setCapturedWhite(newState.captured_white || []);
    if (newState.board_config) {
      setBoardConfig(newState.board_config);
      setPreset(newState.board_config.preset || 'classic');
      setCustomRows(newState.board_config.rows || 10);
      setCustomColumns(newState.board_config.columns || 10);
    }
  };

  useEffect(() => {
    if (store.strategoBoard) {
      updateStateFromResponse(store.strategoBoard);
    }
  }, [store.strategoBoard]);

  useEffect(() => {
    async function loadBoard() {
      try {
        const res = await fetch('/api/stratego/board');
        const data = await res.json();
        if (data.board) {
          updateStateFromResponse(data);
        }
      } catch (e) {
        console.error('Failed to load Stratego state:', e);
      }
    }
    loadBoard();
  }, []);

  const boardRows = board.length;
  const boardCols = board[0]?.length || 0;

  const getDeploymentRows = () => boardConfig?.initial_rows || 4;
  const isDeploymentCell = (row: number) => {
    if (!boardConfig) return false;
    return row >= boardRows - getDeploymentRows();
  };

  const computeValidMoves = (row: number, col: number) => {
    const cell = board[row][col];
    if (!isOwnCell(cell) || getCode(cell) === 'F' || cell === '##') return [];
    const moves: { row: number; col: number }[] = [];
    for (const [dr, dc] of [
      [-1, 0],
      [1, 0],
      [0, -1],
      [0, 1],
    ] as const) {
      const nr = row + dr;
      const nc = col + dc;
      if (nr < 0 || nr >= boardRows || nc < 0 || nc >= boardCols) continue;
      const target = board[nr][nc];
      if (target === '##' || isOwnCell(target)) continue;
      moves.push({ row: nr, col: nc });
    }
    return moves;
  };

  const startNewGame = async () => {
    try {
      const payload: any = { difficulty, preset };
      if (preset === 'custom') {
        payload.rows = customRows;
        payload.columns = customColumns;
        payload.piece_counts = customPieceCounts;
      }
      const res = await fetch('/api/stratego/new', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      const newState = data.board || data;
      if (newState.board) {
        updateStateFromResponse(newState);
        setSelected(null);
        setValidMoves([]);
        setErrorMessage(null);
        setSaveMessage(null);
      }
    } catch (e) {
      console.error('Failed to start Stratego game:', e);
    }
  };

  const placePieceOnBoard = async (row: number, col: number) => {
    if (!selectedSetupPiece || (deploymentCounts[selectedSetupPiece] || 0) <= 0) {
      setErrorMessage('Select a piece with remaining deployment count.');
      return;
    }
    setErrorMessage(null);
    try {
      const res = await fetch('/api/stratego/place', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ row, col, piece: selectedSetupPiece }),
      });
      const data = await res.json();
      if (data?.board) {
        updateStateFromResponse(data);
      }
      if (data?.error) {
        setErrorMessage(data.error);
      }
    } catch (e) {
      console.error('Place piece failed:', e);
      setErrorMessage('Unable to place the piece.');
    }
  };

  const removePieceFromBoard = async (row: number, col: number) => {
    try {
      const res = await fetch('/api/stratego/remove', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ row, col }),
      });
      const data = await res.json();
      if (data?.board) {
        updateStateFromResponse(data);
      }
      if (data?.error) {
        setErrorMessage(data.error);
      }
    } catch (e) {
      console.error('Remove piece failed:', e);
      setErrorMessage('Unable to remove the piece.');
    }
  };

  const beginBattle = async () => {
    if (Object.values(deploymentCounts).some((count) => count > 0)) {
      setErrorMessage('You must deploy all remaining pieces before beginning the battle.');
      return;
    }
    setErrorMessage(null);
    try {
      const res = await fetch('/api/stratego/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });
      const data = await res.json();
      if (data?.board) {
        updateStateFromResponse(data);
        setSelected(null);
        setValidMoves([]);
      }
      if (data?.error) {
        setErrorMessage(data.error);
      }
    } catch (e) {
      console.error('Start battle failed:', e);
      setErrorMessage('Unable to begin the battle.');
    }
  };

  const saveGame = async () => {
    try {
      const res = await fetch('/api/stratego/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({}),
      });
      const data = await res.json();
      setSaveMessage(data.message || 'Game saved.');
      if (data?.board) {
        updateStateFromResponse(data);
      }
      if (data?.error) {
        setErrorMessage(data.error);
      }
    } catch (e) {
      console.error('Save failed:', e);
      setSaveMessage('Save failed.');
    }
  };

  const loadGame = async () => {
    try {
      const res = await fetch('/api/stratego/load', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({}),
      });
      const data = await res.json();
      if (data?.board) {
        updateStateFromResponse(data);
      }
      if (data?.error) {
        setErrorMessage(data.error);
      }
    } catch (e) {
      console.error('Load failed:', e);
      setErrorMessage('Unable to load saved game.');
    }
  };

  const handleCellClick = async (row: number, col: number) => {
    if (gameOver) return;
    const cell = board[row][col];

    if (setupPhase) {
      if (isDeploymentCell(row) && cell === '.') {
        await placePieceOnBoard(row, col);
        return;
      }
      if (isDeploymentCell(row) && isOwnCell(cell)) {
        await removePieceFromBoard(row, col);
        return;
      }
      return;
    }

    if (selected) {
      const isMove = validMoves.some((move) => move.row === row && move.col === col);
      if (isMove) {
        try {
          const res = await fetch('/api/stratego/move', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ from_row: selected.row, from_col: selected.col, to_row: row, to_col: col }),
          });
          const data = await res.json();
          if (data?.board) {
            setBoard(data.board);
          }
          setSelected(null);
          setValidMoves([]);
          if (data?.error) {
            setErrorMessage(data.error);
          }
        } catch (e) {
          console.error('Move failed:', e);
          setErrorMessage('Unable to move piece.');
        }
        return;
      }
    }

    if (isOwnCell(cell)) {
      const moves = computeValidMoves(row, col);
      setSelected({ row, col });
      setValidMoves(moves);
    } else {
      setSelected(null);
      setValidMoves([]);
    }
  };

  const isHighlighted = (row: number, col: number) => selected?.row === row && selected?.col === col;
  const isMoveTarget = (row: number, col: number) => validMoves.some((move) => move.row === row && move.col === col);

  const revealRules = useMemo(
    () => [
      'Only your own pieces are visible. Sarah only sees her side and the enemy pieces she has uncovered in combat.',
      'Pieces move one square orthogonally. Flags cannot move.',
      'When opposing pieces meet, the higher-ranking piece wins and remains. Equal strength removes both.',
      'Spy can defeat the Marshal (10) when attacking, otherwise it loses.',
      'Capture the enemy flag to win, or leave Sarah with no legal moves.',
    ],
    [],
  );

  const renderPiece = (cell: string) => {
    if (cell === '.' || cell === '##') return null;
    if (cell === 'b?') return <span className="text-slate-400">?</span>;
    const code = getCode(cell);
    return <span className="font-semibold">{pieceLabels[code] || code}</span>;
  };

  const getPieceClass = (cell: string) => {
    if (cell === '##') return 'text-sky-200/80';
    if (cell === 'b?') return 'text-slate-400';
    if (cell.startsWith('w')) return 'text-amber-200';
    if (cell.startsWith('b')) return 'text-slate-300';
    return 'text-white/30';
  };

  const totalRemaining = Object.values(pieceCounts).reduce((sum, count) => sum + count, 0);

  return (
    <div className="h-full flex flex-col px-4 py-4 overflow-hidden">
      <div className="flex items-center justify-between mb-3 gap-2">
        <div className="flex items-center gap-2">
          <Shield className="w-5 h-5 text-cyan-300" />
          <div>
            <h2 className="text-lg font-semibold text-white">Stratego</h2>
            <p className="text-xs text-slate-400">Hidden piece combat with adjustable AI difficulty.</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button onClick={startNewGame} size="sm" className="bg-amber-500/20 hover:bg-amber-500/30 text-amber-300 border border-amber-500/30">
            <RotateCcw className="w-3 h-3 mr-1" /> New Game
          </Button>
          <Button onClick={saveGame} size="sm" className="bg-slate-700/70 hover:bg-slate-700 text-white/90 border border-white/10">
            Save Game
          </Button>
          <Button onClick={loadGame} size="sm" className="bg-slate-700/70 hover:bg-slate-700 text-white/90 border border-white/10">
            Load Game
          </Button>
          <Button
            size="sm"
            variant="secondary"
            className="bg-white/5 hover:bg-white/10 text-white/70"
            onClick={() => setShowRules((value) => !value)}
          >
            <HelpCircle className="w-3.5 h-3.5 mr-1" /> Rules
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-3 mb-4 text-slate-200 text-xs">
        <div className="rounded-2xl border border-white/10 bg-slate-950/60 p-3">
          <div className="text-[11px] text-slate-400 mb-2">Board Preset</div>
          <select
            value={preset}
            onChange={(event) => setPreset(event.target.value)}
            className="w-full rounded-xl border border-white/10 bg-slate-900 px-3 py-2 text-sm text-white"
          >
            {presetOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>
        <div className="rounded-2xl border border-white/10 bg-slate-950/60 p-3">
          <div className="text-[11px] text-slate-400 mb-2">Board Size</div>
          <div className="flex items-center gap-2">
            <input
              type="number"
              min={8}
              max={16}
              value={customRows}
              onChange={(event) => setCustomRows(Number(event.target.value))}
              disabled={preset !== 'custom'}
              className="w-1/2 rounded-xl border border-white/10 bg-slate-900 px-3 py-2 text-white"
            />
            <input
              type="number"
              min={8}
              max={16}
              value={customColumns}
              onChange={(event) => setCustomColumns(Number(event.target.value))}
              disabled={preset !== 'custom'}
              className="w-1/2 rounded-xl border border-white/10 bg-slate-900 px-3 py-2 text-white"
            />
          </div>
          <div className="mt-2 text-[11px] text-slate-500">Custom mode supports larger or smaller boards.</div>
        </div>
        <div className="rounded-2xl border border-white/10 bg-slate-950/60 p-3">
          <div className="text-[11px] text-slate-400 mb-2">Map Details</div>
          <div className="text-sm text-white">
            {boardConfig?.preset === 'classic'
              ? 'Classic lakes and bomb setup'
              : boardConfig?.preset === 'open'
              ? 'Open field, no lakes'
              : 'Custom board'}
          </div>
          <div className="mt-2 text-slate-400">{boardConfig?.rows}×{boardConfig?.columns} board</div>
          <div className="mt-2 text-slate-400">{boardConfig?.obstacles?.length || 0} lake squares</div>
        </div>
      </div>

      {preset === 'custom' && (
        <div className="mb-4 rounded-2xl border border-white/10 bg-slate-950/60 p-4 text-xs text-slate-300">
          <div className="mb-3 text-sm font-semibold text-white">Custom Piece Ratios</div>
          <div className="grid grid-cols-4 gap-2">
            {pieceOrder.map((code) => (
              <label key={code} className="flex flex-col rounded-xl border border-white/10 bg-slate-900 p-2 text-[11px]">
                <span className="text-slate-400">{pieceNames[code]}</span>
                <input
                  type="number"
                  min={0}
                  max={20}
                  value={customPieceCounts[code] ?? 0}
                  onChange={(event) => setCustomPieceCounts((prev) => ({ ...prev, [code]: Number(event.target.value) }))}
                  className="mt-1 rounded-xl border border-white/10 bg-slate-800 px-2 py-1 text-white"
                />
              </label>
            ))}
          </div>
          <div className="mt-3 text-[11px] text-slate-500">Adjust how many of each unit are available for your custom board. Bombs and your flag remain part of the setup.</div>
        </div>
      )}

      <div className="grid grid-cols-2 gap-3 mb-4">
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-xs text-slate-300">
            <span className="font-semibold text-white">Difficulty</span>
            <Badge variant="outline" className="text-xs text-white/80">
              {difficultyLabels[difficulty]}
            </Badge>
          </div>
          <input
            type="range"
            min={1}
            max={6}
            value={difficulty}
            onChange={(event) => setDifficulty(Number(event.target.value))}
            className="w-full accent-cyan-400"
          />
          <p className="text-[11px] text-slate-400">Move slowly and reveal enemy pieces to win. Sarah uses a strength-aware hidden information policy.</p>
        </div>
        <div className="space-y-2 text-xs text-slate-300">
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="text-xs text-white/80">You</Badge>
            <span>{totalRemaining} pieces remaining</span>
          </div>
          <div className="grid grid-cols-3 gap-2">
            {pieceOrder.map((code) => (
              <div key={code} className="rounded-md border border-white/10 bg-white/5 p-2 text-center text-[11px] text-slate-200">
                <span className="block font-semibold text-white">{pieceLabels[code]}</span>
                <span className="block text-slate-400">{pieceNames[code]}</span>
                <span className="block text-cyan-200">{pieceCounts[code] || 0}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {showRules && (
        <div className="mb-4 rounded-2xl border border-cyan-500/20 bg-slate-950/40 p-4 text-sm text-slate-200">
          <div className="mb-3 flex items-center gap-2 text-white text-sm font-semibold">Game Rules</div>
          <ul className="space-y-2 list-disc pl-5 text-slate-300">
            {revealRules.map((rule) => (
              <li key={rule}>{rule}</li>
            ))}
          </ul>
          <div className="mt-3 text-xs text-slate-500">Spy special: the Spy defeats the Marshal (10) when it attacks. Otherwise higher rank wins.</div>
        </div>
      )}

      {setupPhase && (
        <div className="mb-4 rounded-2xl border border-amber-500/20 bg-slate-950/60 p-4 text-sm text-slate-200">
          <div className="mb-3 flex items-center justify-between gap-4">
            <div>
              <div className="text-sm font-semibold text-white">Deployment Phase</div>
              <div className="text-xs text-slate-400">Place remaining pieces into the last {getDeploymentRows()} rows of the board.</div>
            </div>
            <Button
              onClick={beginBattle}
              size="sm"
              className="bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-300 border border-emerald-500/30"
              disabled={Object.values(deploymentCounts).some((count) => count > 0)}
            >
              Begin Battle
            </Button>
          </div>
          <div className="grid grid-cols-6 gap-2 mb-3">
            {pieceOrder.map((code) => (
              <button
                key={code}
                type="button"
                onClick={() => setSelectedSetupPiece(code)}
                className={`rounded-2xl border p-2 text-xs text-left transition ${selectedSetupPiece === code ? 'border-cyan-400 bg-slate-800' : 'border-white/10 bg-slate-900/70'}`}
              >
                <div className="font-semibold text-white">{pieceLabels[code]}</div>
                <div className="text-slate-400">{pieceNames[code]}</div>
                <div className="mt-1 text-[11px] text-slate-300">{deploymentCounts[code] ?? 0} left</div>
              </button>
            ))}
          </div>
          <div className="text-xs text-slate-400">
            Selected: <span className="text-white">{pieceNames[selectedSetupPiece]}</span> ({deploymentCounts[selectedSetupPiece] ?? 0} left)
          </div>
          {errorMessage && (
            <div className="mt-3 rounded-xl border border-rose-500/20 bg-rose-500/10 p-3 text-rose-200">{errorMessage}</div>
          )}
        </div>
      )}

      {saveMessage && (
        <div className="mb-4 rounded-2xl border border-cyan-500/20 bg-slate-950/60 p-3 text-sm text-cyan-200">
          {saveMessage}
        </div>
      )}

      <div className="flex-1 flex flex-col gap-4 overflow-hidden">
        <div
          className="grid gap-[1px] rounded-xl overflow-hidden border border-white/10 bg-slate-900/80 shadow-lg"
          style={{ gridTemplateColumns: `repeat(${boardCols}, minmax(0, 1fr))` }}
        >
          {board.map((row, rowIndex) =>
            row.map((cell, colIndex) => {
              const isSelected = isHighlighted(rowIndex, colIndex);
              const canMove = isMoveTarget(rowIndex, colIndex);
              const isDark = (rowIndex + colIndex) % 2 === 1;
              const isDeploymentSquare = setupPhase && isDeploymentCell(rowIndex);
              const cellBg = cell === '##'
                ? 'bg-sky-900/80'
                : isDeploymentSquare
                ? 'bg-amber-950/80'
                : isDark
                ? 'bg-slate-900/70'
                : 'bg-slate-800/80';
              return (
                <button
                  key={`${rowIndex}-${colIndex}`}
                  type="button"
                  onClick={() => handleCellClick(rowIndex, colIndex)}
                  className={`relative aspect-square w-full rounded-none border-none p-0 text-xs text-center transition ${cellBg} ${
                    isSelected ? 'ring-2 ring-cyan-400/80' : ''
                  } ${canMove ? 'ring-1 ring-emerald-400/70' : ''} ${isDeploymentSquare ? 'hover:bg-amber-500/10' : 'hover:brightness-110'}`}
                >
                  <div className="flex h-full flex-col items-center justify-center">
                    <span className={getPieceClass(cell)}>{renderPiece(cell)}</span>
                  </div>
                  {cell === '##' && <div className="absolute inset-0 bg-sky-800/40" />}
                  {canMove && cell === '.' && (
                    <div className="absolute inset-0 flex items-center justify-center">
                      <span className="h-2 w-2 rounded-full bg-emerald-400/80" />
                    </div>
                  )}
                </button>
              );
            }),
          )}
        </div>

        <div className="grid grid-cols-3 gap-3 text-xs text-slate-200">
          <div className="rounded-2xl border border-white/10 bg-slate-950/60 p-3">
            <div className="text-[11px] text-slate-400">Turn</div>
            <div className="mt-1 text-sm font-semibold text-white">{currentPlayer === 'white' ? 'Your Turn' : "Sarah's Turn"}</div>
          </div>
          <div className="rounded-2xl border border-white/10 bg-slate-950/60 p-3">
            <div className="text-[11px] text-slate-400">Captured</div>
            <div className="mt-1 text-sm font-semibold text-white">{capturedWhite.length}</div>
            <div className="text-[11px] text-slate-400">Enemy lost</div>
          </div>
          <div className="rounded-2xl border border-white/10 bg-slate-950/60 p-3">
            <div className="text-[11px] text-slate-400">Status</div>
            <div className="mt-1 text-sm font-semibold text-white">
              {gameOver ? (winner === 'white' ? 'You won' : 'Sarah won') : 'In progress'}
            </div>
          </div>
        </div>

        <div className="rounded-2xl border border-white/10 bg-slate-950/60 p-3 text-xs text-slate-300">
          <div className="font-semibold text-white mb-2">Combat Notes</div>
          <p>Opponent pieces are hidden until combat reveals them. Use your flag and high-rank forces carefully, and beware the Spy against the Marshal.</p>
        </div>
      </div>
    </div>
  );
}
