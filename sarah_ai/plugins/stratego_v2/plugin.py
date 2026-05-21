import copy
import json
import random
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

DEFAULT_PIECE_COUNTS = {
    'F': 1,  # Flag
    'S': 1,  # Spy
    'N': 1,  # Marshal (10)
    'G': 1,  # General (9)
    'C': 2,  # Colonel (8)
    'M': 3,  # Major (7)
    'A': 4,  # Captain (6)
    'L': 4,  # Lieutenant (5)
    'E': 4,  # Sergeant (4)
    'R': 5,  # Miner (3)
    'O': 8,  # Scout (2)
    'P': 10, # Private (1)
    'B': 6,  # Bomb
}

PIECE_RANKS = {
    'F': 0,
    'S': 1,
    'P': 1,
    'O': 2,
    'R': 3,
    'E': 4,
    'L': 5,
    'A': 6,
    'M': 7,
    'C': 8,
    'G': 9,
    'N': 10,
    'B': 0,
}

PIECE_NAMES = {
    'F': 'Flag',
    'S': 'Spy',
    'N': 'Marshal',
    'G': 'General',
    'C': 'Colonel',
    'M': 'Major',
    'A': 'Captain',
    'L': 'Lieutenant',
    'E': 'Sergeant',
    'R': 'Miner',
    'O': 'Scout',
    'P': 'Private',
    'B': 'Bomb',
}

DIFFICULTY_CONFIG = {
    1: {'label': 'Easy', 'randomness': 0.45, 'risk_tolerance': 0.7},
    2: {'label': 'Casual', 'randomness': 0.35, 'risk_tolerance': 0.65},
    3: {'label': 'Normal', 'randomness': 0.22, 'risk_tolerance': 0.55},
    4: {'label': 'Hard', 'randomness': 0.1, 'risk_tolerance': 0.45},
    5: {'label': 'Very Hard', 'randomness': 0.05, 'risk_tolerance': 0.35},
    6: {'label': 'Impossible', 'randomness': 0.0, 'risk_tolerance': 0.25},
}

PRESET_CONFIGS = {
    'classic': {
        'rows': 10,
        'columns': 10,
        'initial_rows': 4,
        'obstacles': [(4, 2), (5, 2), (4, 3), (5, 3), (4, 6), (5, 6), (4, 7), (5, 7)],
        'piece_counts': copy.deepcopy(DEFAULT_PIECE_COUNTS),
    },
    'open': {
        'rows': 10,
        'columns': 10,
        'initial_rows': 4,
        'obstacles': [],
        'piece_counts': copy.deepcopy(DEFAULT_PIECE_COUNTS),
    },
}

DEFAULT_PRESET = 'classic'

class StrategoGame:
    SAVE_PATH = Path(__file__).resolve().parents[1] / 'memory' / 'stratego_saved.json'

    def __init__(self) -> None:
        self.reset_game(3)

    def reset_game(
        self,
        difficulty: int = 3,
        preset: str = DEFAULT_PRESET,
        rows: Optional[int] = None,
        columns: Optional[int] = None,
        piece_counts: Optional[Dict[str, int]] = None,
        manual_setup: bool = True,
        obstacles: Optional[List[Tuple[int, int]]] = None,
    ) -> Dict[str, Any]:
        self.current_player = 'white'
        self.difficulty = int(difficulty) if isinstance(difficulty, int) else 3
        self.game_over = False
        self.winner: Optional[str] = None
        self.move_history: List[str] = []
        self.captured_white: List[str] = []
        self.captured_black: List[str] = []
        self.board_config = self._build_board_config(preset, rows, columns, piece_counts, obstacles)
        self.setup_phase = bool(manual_setup)
        self.deployment_counts = copy.deepcopy(self.board_config['piece_counts'])
        self.revealed = [[False] * self.board_config['columns'] for _ in range(self.board_config['rows'])]
        self.known_white_counts = copy.deepcopy(self.board_config['piece_counts'])
        self.board = [['.' for _ in range(self.board_config['columns'])] for _ in range(self.board_config['rows'])]
        self._place_obstacles()
        if self.setup_phase:
            self._place_random_setup(enemy_only=True)
        else:
            self._place_random_setup()
        return self.get_board_state()

    def get_info(self) -> Dict[str, Any]:
        return {
            'name': 'Stratego',
            'description': 'Play a premium Stratego-style game with classic lakes, bombs, manual deployment, custom maps, and hidden enemy information.',
            'version': '2.0',
        }

    def get_board_state(self) -> Dict[str, Any]:
        return {
            'board': self._public_board_view(),
            'current_player': self.current_player,
            'move_history': self.move_history,
            'captured_white': self.captured_white,
            'captured_black': self.captured_black,
            'game_over': self.game_over,
            'winner': self.winner,
            'difficulty': DIFFICULTY_CONFIG.get(self.difficulty, {}).get('label', 'Normal'),
            'piece_counts': self._remaining_piece_counts(),
            'deployment_counts': copy.deepcopy(self.deployment_counts),
            'setup_phase': self.setup_phase,
            'board_config': {
                'preset': self.board_config['preset'],
                'rows': self.board_config['rows'],
                'columns': self.board_config['columns'],
                'initial_rows': self.board_config['initial_rows'],
                'obstacles': self.board_config['obstacles'],
                'piece_counts': self.board_config['piece_counts'],
            },
        }

    def _build_board_config(
        self,
        preset: str,
        rows: Optional[int],
        columns: Optional[int],
        piece_counts: Optional[Dict[str, int]],
        obstacles: Optional[List[Tuple[int, int]]],
    ) -> Dict[str, Any]:
        preset_key = preset.lower() if isinstance(preset, str) else DEFAULT_PRESET
        base_config = copy.deepcopy(PRESET_CONFIGS.get(preset_key, PRESET_CONFIGS[DEFAULT_PRESET]))
        if rows is not None:
            base_config['rows'] = max(8, min(16, int(rows)))
        if columns is not None:
            base_config['columns'] = max(8, min(16, int(columns)))
        if piece_counts:
            normalized: Dict[str, int] = {}
            for code, count in piece_counts.items():
                if code in DEFAULT_PIECE_COUNTS:
                    normalized[code] = max(0, int(count))
            for code, default_count in DEFAULT_PIECE_COUNTS.items():
                normalized.setdefault(code, default_count)
            base_config['piece_counts'] = normalized
        if obstacles is not None:
            valid_obstacles: List[Tuple[int, int]] = []
            for row, col in obstacles:
                if 0 <= row < base_config['rows'] and 0 <= col < base_config['columns']:
                    valid_obstacles.append((row, col))
            base_config['obstacles'] = valid_obstacles
        base_config['preset'] = preset_key
        return base_config

    def _place_obstacles(self) -> None:
        for row, col in self.board_config['obstacles']:
            if 0 <= row < self.board_config['rows'] and 0 <= col < self.board_config['columns']:
                self.board[row][col] = '##'

    def _remaining_piece_counts(self) -> Dict[str, Dict[str, int]]:
        counts = {'white': {}, 'black': {}, 'revealed_enemy': {}}
        for row in range(self.board_config['rows']):
            for col in range(self.board_config['columns']):
                cell = self.board[row][col]
                if cell in ('.', '##'):
                    continue
                owner = cell[0]
                code = cell[1:]
                if owner == 'w':
                    counts['white'][code] = counts['white'].get(code, 0) + 1
                else:
                    counts['black'][code] = counts['black'].get(code, 0) + 1
                    if self.revealed[row][col]:
                        counts['revealed_enemy'][code] = counts['revealed_enemy'].get(code, 0) + 1
        return counts

    def _place_random_setup(self, enemy_only: bool = False) -> None:
        piece_pool: List[str] = []
        for code, count in self.board_config['piece_counts'].items():
            piece_pool.extend([code] * count)
        random.shuffle(piece_pool)

        if enemy_only:
            for row in range(0, self.board_config['initial_rows']):
                for col in range(self.board_config['columns']):
                    if not piece_pool:
                        break
                    if self.board[row][col] != '.':
                        continue
                    self.board[row][col] = 'b' + piece_pool.pop()
            return

        for row in range(self.board_config['rows'] - self.board_config['initial_rows'], self.board_config['rows']):
            for col in range(self.board_config['columns']):
                if not piece_pool:
                    break
                if self.board[row][col] != '.':
                    continue
                self.board[row][col] = 'w' + piece_pool.pop()

        for row in range(0, self.board_config['initial_rows']):
            for col in range(self.board_config['columns']):
                if not piece_pool:
                    break
                if self.board[row][col] != '.':
                    continue
                self.board[row][col] = 'b' + piece_pool.pop()

    def _public_board_view(self) -> List[List[str]]:
        view: List[List[str]] = []
        for row in range(self.board_config['rows']):
            view_row: List[str] = []
            for col in range(self.board_config['columns']):
                cell = self.board[row][col]
                if cell == '.':
                    view_row.append('.')
                    continue
                if cell == '##':
                    view_row.append('##')
                    continue
                owner = cell[0]
                if owner == 'w':
                    view_row.append(cell)
                else:
                    view_row.append(cell if self.revealed[row][col] else 'b?')
            view.append(view_row)
        return view

    def _is_valid_position(self, row: int, col: int) -> bool:
        return 0 <= row < self.board_config['rows'] and 0 <= col < self.board_config['columns']

    def _get_owner(self, cell: str) -> Optional[str]:
        if cell in ('.', '##'):
            return None
        return 'white' if cell.startswith('w') else 'black'

    def _get_piece_code(self, cell: str) -> str:
        if cell in ('.', '##'):
            return '.'
        return cell[1:]

    def _is_movable(self, cell: str) -> bool:
        if cell in ('.', '##'):
            return False
        code = self._get_piece_code(cell)
        return code not in ('F', 'B')

    def _get_valid_moves(self, row: int, col: int) -> List[Tuple[int, int]]:
        cell = self.board[row][col]
        if not self._is_movable(cell):
            return []
        owner = self._get_owner(cell)
        if owner != self.current_player:
            return []

        moves: List[Tuple[int, int]] = []
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = row + dr, col + dc
            if not self._is_valid_position(nr, nc):
                continue
            target = self.board[nr][nc]
            if target == '##':
                continue
            target_owner = self._get_owner(target)
            if target_owner == owner:
                continue
            moves.append((nr, nc))
        return moves

    def _battle_outcome(self, attacker: str, defender: str) -> str:
        attacker_code = self._get_piece_code(attacker)
        defender_code = self._get_piece_code(defender)

        if defender_code == 'F':
            return 'attacker'

        if defender_code == 'B':
            return 'attacker' if attacker_code == 'R' else 'defender'

        if attacker_code == 'S' and defender_code == 'N':
            return 'attacker'

        if defender_code == 'S' and attacker_code != 'N':
            return 'defender'

        attacker_rank = PIECE_RANKS.get(attacker_code, 0)
        defender_rank = PIECE_RANKS.get(defender_code, 0)

        if attacker_rank > defender_rank:
            return 'attacker'
        if attacker_rank < defender_rank:
            return 'defender'
        return 'both'

    def _record_reveal(self, row: int, col: int) -> None:
        if self.board[row][col] != '##' and self._get_owner(self.board[row][col]) == 'black':
            self.revealed[row][col] = True

    def _deployment_zone(self, row: int, col: int) -> bool:
        return row >= self.board_config['rows'] - self.board_config['initial_rows'] and 0 <= col < self.board_config['columns']

    def _is_white_piece(self, cell: str) -> bool:
        return cell.startswith('w')

    def place_piece(self, row: int, col: int, code: str) -> Dict[str, Any]:
        if not self.setup_phase:
            return {'success': False, 'error': 'Setup phase is not active', 'board': self.get_board_state()}
        if not self._is_valid_position(row, col):
            return {'success': False, 'error': 'Invalid board coordinates', 'board': self.get_board_state()}
        if not self._deployment_zone(row, col):
            return {'success': False, 'error': 'Piece must be placed within your deployment zone', 'board': self.get_board_state()}
        if self.board[row][col] != '.':
            return {'success': False, 'error': 'Deployment cell is not empty', 'board': self.get_board_state()}
        if code not in self.deployment_counts or self.deployment_counts[code] <= 0:
            return {'success': False, 'error': 'No remaining pieces of that type', 'board': self.get_board_state()}

        self.board[row][col] = 'w' + code
        self.deployment_counts[code] -= 1
        return {'success': True, 'message': 'Piece placed', 'board': self.get_board_state()}

    def remove_piece(self, row: int, col: int) -> Dict[str, Any]:
        if not self.setup_phase:
            return {'success': False, 'error': 'Setup phase is not active', 'board': self.get_board_state()}
        if not self._is_valid_position(row, col):
            return {'success': False, 'error': 'Invalid board coordinates', 'board': self.get_board_state()}
        cell = self.board[row][col]
        if not self._is_white_piece(cell):
            return {'success': False, 'error': 'No white piece to remove', 'board': self.get_board_state()}
        code = self._get_piece_code(cell)
        if code not in self.deployment_counts:
            return {'success': False, 'error': 'Invalid piece code', 'board': self.get_board_state()}

        self.board[row][col] = '.'
        self.deployment_counts[code] += 1
        return {'success': True, 'message': 'Piece removed', 'board': self.get_board_state()}

    def begin_game(self) -> Dict[str, Any]:
        if not self.setup_phase:
            return {'success': False, 'error': 'Game already started', 'board': self.get_board_state()}
        if any(count > 0 for count in self.deployment_counts.values()):
            return {'success': False, 'error': 'All pieces must be placed before starting', 'board': self.get_board_state()}
        self.setup_phase = False
        self.current_player = 'white'
        return self.get_board_state()

    def save_game(self) -> Dict[str, Any]:
        try:
            self.SAVE_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(self.SAVE_PATH, 'w', encoding='utf-8') as f:
                json.dump(self._serialize_state(), f, indent=2)
            return {'success': True, 'message': 'Game saved successfully', 'board': self.get_board_state()}
        except Exception as e:
            return {'success': False, 'error': str(e), 'board': self.get_board_state()}

    def load_game(self) -> Dict[str, Any]:
        try:
            if not self.SAVE_PATH.exists():
                return {'success': False, 'error': 'No saved game available', 'board': self.get_board_state()}
            with open(self.SAVE_PATH, 'r', encoding='utf-8') as f:
                state = json.load(f)
            self._load_state(state)
            return {'success': True, 'message': 'Game loaded successfully', 'board': self.get_board_state()}
        except Exception as e:
            return {'success': False, 'error': str(e), 'board': self.get_board_state()}

    def _serialize_state(self) -> Dict[str, Any]:
        return {
            'current_player': self.current_player,
            'difficulty': self.difficulty,
            'game_over': self.game_over,
            'winner': self.winner,
            'move_history': self.move_history,
            'captured_white': self.captured_white,
            'captured_black': self.captured_black,
            'board_config': self.board_config,
            'board': self.board,
            'revealed': self.revealed,
            'known_white_counts': self.known_white_counts,
            'setup_phase': self.setup_phase,
            'deployment_counts': self.deployment_counts,
        }

    def _load_state(self, state: Dict[str, Any]) -> None:
        self.current_player = state.get('current_player', 'white')
        self.difficulty = state.get('difficulty', 3)
        self.game_over = state.get('game_over', False)
        self.winner = state.get('winner')
        self.move_history = state.get('move_history', [])
        self.captured_white = state.get('captured_white', [])
        self.captured_black = state.get('captured_black', [])
        self.board_config = state.get('board_config', self.board_config)
        self.board = state.get('board', self.board)
        self.revealed = state.get('revealed', self.revealed)
        self.known_white_counts = state.get('known_white_counts', self.known_white_counts)
        self.setup_phase = state.get('setup_phase', False)
        self.deployment_counts = state.get('deployment_counts', copy.deepcopy(self.board_config['piece_counts']))

    def make_move(self, from_row: int, from_col: int, to_row: int, to_col: int, auto_ai: bool = True) -> Dict[str, Any]:
        if self.setup_phase:
            return {'success': False, 'error': 'Game has not started. Complete deployment and begin the game first.', 'board': self.get_board_state()}
        if self.game_over:
            return {'success': False, 'error': 'Game is over', 'board': self.get_board_state()}

        if not self._is_valid_position(from_row, from_col) or not self._is_valid_position(to_row, to_col):
            return {'success': False, 'error': 'Invalid board coordinates', 'board': self.get_board_state()}

        source = self.board[from_row][from_col]
        if source in ('.', '##'):
            return {'success': False, 'error': 'No piece at the source square', 'board': self.get_board_state()}

        if self._get_owner(source) != self.current_player:
            return {'success': False, 'error': 'That is not your piece', 'board': self.get_board_state()}

        if not self._is_movable(source):
            return {'success': False, 'error': 'That piece cannot move', 'board': self.get_board_state()}

        if (to_row, to_col) not in self._get_valid_moves(from_row, from_col):
            return {'success': False, 'error': 'Invalid move', 'board': self.get_board_state()}

        destination = self.board[to_row][to_col]
        if destination == '##':
            return {'success': False, 'error': 'Cannot move into a lake', 'board': self.get_board_state()}

        battle_message = 'Moved without conflict.'
        if destination != '.':
            outcome = self._battle_outcome(source, destination)
            self._record_reveal(to_row, to_col)
            if self.current_player == 'black':
                self._reveal_white_piece(destination)

            if outcome == 'attacker':
                if self.current_player == 'white':
                    self.captured_black.append(self._get_piece_code(destination))
                else:
                    self.captured_white.append(self._get_piece_code(destination))
                self.board[to_row][to_col] = source
                self.board[from_row][from_col] = '.'
                battle_message = f"{PIECE_NAMES[self._get_piece_code(source)]} defeated {PIECE_NAMES[self._get_piece_code(destination)]}."
            elif outcome == 'defender':
                if self.current_player == 'white':
                    self.captured_white.append(self._get_piece_code(source))
                else:
                    self.captured_black.append(self._get_piece_code(source))
                self.board[from_row][from_col] = '.'
                battle_message = f"{PIECE_NAMES[self._get_piece_code(destination)]} defended successfully against {PIECE_NAMES[self._get_piece_code(source)]}."
            else:
                self.board[from_row][from_col] = '.'
                self.board[to_row][to_col] = '.'
                if self.current_player == 'white':
                    self.captured_white.append(self._get_piece_code(source))
                    self.captured_black.append(self._get_piece_code(destination))
                else:
                    self.captured_white.append(self._get_piece_code(destination))
                    self.captured_black.append(self._get_piece_code(source))
                battle_message = 'Both pieces were removed in equal strength combat.'

            if destination != '.' and self._get_piece_code(destination) == 'F' and outcome == 'attacker':
                self.game_over = True
                self.winner = self.current_player
                battle_message = f"{self.current_player.capitalize()} captured the flag and won the game!"
        else:
            self.board[to_row][to_col] = source
            self.board[from_row][from_col] = '.'

        self.move_history.append(f"{self.current_player.capitalize()} {from_row},{from_col} → {to_row},{to_col}")
        board_state = self.get_board_state()
        result = self._normalize_move_result(True, battle_message, (from_row, from_col), (to_row, to_col), board_state)

        self.current_player = 'black' if self.current_player == 'white' else 'white'
        if not self.game_over and self._no_moves_available(self.current_player):
            self.game_over = True
            self.winner = 'white' if self.current_player == 'black' else 'black'
            board_state = self.get_board_state()
            result['board'] = board_state
            result['message'] += ' The opponent has no moves left.'

        if self.current_player == 'black' and not self.game_over and auto_ai:
            ai_result = self.ai_move()
            return {'player_move': result, 'ai_move': ai_result, 'board': ai_result.get('board', board_state)}

        return {'player_move': result, 'board': board_state}

    def _reveal_white_piece(self, cell: str) -> None:
        if cell in ('.', '##') or not cell.startswith('w'):
            return
        piece_code = self._get_piece_code(cell)
        if piece_code in self.known_white_counts:
            self.known_white_counts[piece_code] = max(0, self.known_white_counts[piece_code] - 1)

    def _no_moves_available(self, player: str) -> bool:
        for row in range(self.board_config['rows']):
            for col in range(self.board_config['columns']):
                cell = self.board[row][col]
                if self._get_owner(cell) == player and self._get_piece_code(cell) != 'F':
                    if self._get_valid_moves(row, col):
                        return False
        return True

    def _average_unknown_rank(self) -> float:
        total = 0
        pieces = 0
        for code, count in self.known_white_counts.items():
            if code == 'F':
                continue
            rank = PIECE_RANKS.get(code, 0)
            total += rank * count
            pieces += count
        return (total / pieces) if pieces > 0 else 1.0

    def _evaluate_move(self, from_row: int, from_col: int, to_row: int, to_col: int) -> float:
        source = self.board[from_row][from_col]
        target = self.board[to_row][to_col]
        code = self._get_piece_code(source)
        base_score = PIECE_RANKS.get(code, 0) * 2.0
        center_row = (self.board_config['rows'] - 1) / 2.0
        center_col = (self.board_config['columns'] - 1) / 2.0
        center_bonus = 0.5 - (abs(center_row - to_row) + abs(center_col - to_col)) * 0.03
        score = base_score + center_bonus

        if target == '.':
            score += 0.5
            unknown_adjacent = 0
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = to_row + dr, to_col + dc
                if self._is_valid_position(nr, nc) and self.board[nr][nc].startswith('w'):
                    unknown_adjacent += 1
            score -= unknown_adjacent * 0.1
            return score

        if target.startswith('w'):
            avg_rank = self._average_unknown_rank()
            attacker_rank = PIECE_RANKS.get(code, 0)
            if code == 'S':
                expected = 2.8 if avg_rank >= 10 else -0.6
            else:
                expected = (attacker_rank - avg_rank) * 0.8
            score += expected
        return score

    def ai_move(self) -> Dict[str, Any]:
        if self.game_over or self.current_player != 'black':
            return {'success': False, 'error': 'Not AI turn', 'board': self.get_board_state()}

        moves = []
        for row in range(self.board_config['rows']):
            for col in range(self.board_config['columns']):
                cell = self.board[row][col]
                if self._get_owner(cell) == 'black':
                    for move in self._get_valid_moves(row, col):
                        moves.append(((row, col), move))

        if not moves:
            self.game_over = True
            self.winner = 'white'
            return {'success': True, 'message': 'Sarah has no moves left.', 'board': self.get_board_state()}

        scored_moves = []
        for source, target in moves:
            scored_moves.append((self._evaluate_move(source[0], source[1], target[0], target[1]), source, target))
        scored_moves.sort(key=lambda item: item[0], reverse=True)

        config = DIFFICULTY_CONFIG.get(self.difficulty, DIFFICULTY_CONFIG[3])
        choice_pool = scored_moves[: max(1, min(len(scored_moves), 4 + int((1 - config['randomness']) * 10)))]
        if not choice_pool:
            choice_pool = scored_moves

        if random.random() < config['randomness']:
            score, src, dst = random.choice(choice_pool)
        else:
            score, src, dst = choice_pool[0]

        from_row, from_col = src
        to_row, to_col = dst
        source_piece = self.board[from_row][from_col]
        target_piece = self.board[to_row][to_col]
        outcome_message = 'Sarah moved her force.'

        if target_piece != '.':
            self._record_reveal(to_row, to_col)
            self._reveal_white_piece(target_piece)
            outcome = self._battle_outcome(source_piece, target_piece)
            if outcome == 'attacker':
                self.captured_white.append(self._get_piece_code(target_piece))
                self.board[to_row][to_col] = source_piece
                self.board[from_row][from_col] = '.'
                outcome_message = f"Sarah's {PIECE_NAMES[self._get_piece_code(source_piece)]} defeated your {PIECE_NAMES[self._get_piece_code(target_piece)]}."
            elif outcome == 'defender':
                self.captured_black.append(self._get_piece_code(source_piece))
                self.board[from_row][from_col] = '.'
                outcome_message = f"Your {PIECE_NAMES[self._get_piece_code(target_piece)]} defended against Sarah's {PIECE_NAMES[self._get_piece_code(source_piece)]}."
            else:
                self.board[from_row][from_col] = '.'
                self.board[to_row][to_col] = '.'
                self.captured_white.append(self._get_piece_code(target_piece))
                self.captured_black.append(self._get_piece_code(source_piece))
                outcome_message = 'Both pieces were removed in a contested fight.'

            if self._get_piece_code(target_piece) == 'F' and outcome == 'attacker':
                self.game_over = True
                self.winner = 'black'
                outcome_message = 'Sarah captured your flag and won the game!'
        else:
            self.board[to_row][to_col] = source_piece
            self.board[from_row][from_col] = '.'

        self.move_history.append(f"Black {from_row},{from_col} → {to_row},{to_col}")
        self.current_player = 'white'
        if not self.game_over and self._no_moves_available('white'):
            self.game_over = True
            self.winner = 'black'
            outcome_message = 'You have no valid moves left. Sarah wins.'

        return {'success': True, 'message': outcome_message, 'move': {'from': {'row': from_row, 'col': from_col}, 'to': {'row': to_row, 'col': to_col}}, 'board': self.get_board_state()}

class StrategoPlugin:
    def __init__(self) -> None:
        self.game = StrategoGame()

    def get_info(self) -> Dict[str, Any]:
        return self.game.get_info()

    def new_game(
        self,
        difficulty: int = 3,
        preset: str = DEFAULT_PRESET,
        rows: Optional[int] = None,
        columns: Optional[int] = None,
        piece_counts: Optional[Dict[str, int]] = None,
    ) -> Dict[str, Any]:
        return self.game.reset_game(difficulty, preset=preset, rows=rows, columns=columns, piece_counts=piece_counts)

    def get_board(self) -> Dict[str, Any]:
        return self.game.get_board_state()

    def make_move(self, from_row: int, from_col: int, to_row: int, to_col: int, auto_ai: bool = True) -> Dict[str, Any]:
        return self.game.make_move(from_row, from_col, to_row, to_col, auto_ai=auto_ai)

    def get_stats(self) -> Dict[str, Any]:
        return {
            'moves': len(self.game.move_history),
            'captured_white': len(self.game.captured_white),
            'captured_black': len(self.game.captured_black),
            'difficulty': DIFFICULTY_CONFIG.get(self.game.difficulty, {}).get('label', 'Normal'),
        }
