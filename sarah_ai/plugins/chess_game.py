import json
import os
import random
import copy
from typing import Dict, List, Optional, Tuple
from datetime import datetime

class ChessGame:
    """
    Full-featured Chess game with AI opponent.
    Uses standard chess rules with minimax AI.
    """
    
    def __init__(self):
        self.reset_game()
        self.game_history = []
        self.save_file = "memory/chess_games.json"
        os.makedirs("memory", exist_ok=True)
    
    def reset_game(self):
        """Initialize a new chess board."""
        # Standard starting position
        self.board = [
            ['r','n','b','q','k','b','n','r'],
            ['p','p','p','p','p','p','p','p'],
            ['.','.','.','.','.','.','.','.'],
            ['.','.','.','.','.','.','.','.'],
            ['.','.','.','.','.','.','.','.'],
            ['.','.','.','.','.','.','.','.'],
            ['P','P','P','P','P','P','P','P'],
            ['R','N','B','Q','K','B','N','R']
        ]
        self.current_player = 'white'
        self.move_history = []
        self.captured_white = []
        self.captured_black = []
        self.game_over = False
        self.winner = None
        self.draw = False
        self.castling_rights = {'K': True, 'Q': True, 'k': True, 'q': True}
        self.en_passant_target = None
        self.halfmove_clock = 0
        self.fullmove_number = 1
        self.position_history = []
    
    def get_info(self) -> Dict:
        return {
            "name": "Chess",
            "description": "Play chess against Sarah",
            "version": "1.0"
        }
    
    def get_board_state(self) -> Dict:
        """Get current board state for frontend."""
        return {
            "board": self.board,
            "current_player": self.current_player,
            "move_history": self.move_history,
            "captured_white": self.captured_white,
            "captured_black": self.captured_black,
            "game_over": self.game_over,
            "winner": self.winner,
            "is_draw": self.draw,
            "valid_moves": self.get_all_valid_moves() if self.current_player == 'white' else []
        }
    
    def _is_valid_pos(self, row: int, col: int) -> bool:
        return 0 <= row < 8 and 0 <= col < 8
    
    def _get_piece_color(self, piece: str) -> Optional[str]:
        if piece == '.':
            return None
        return 'white' if piece.isupper() else 'black'
    
    def _get_valid_moves_for_piece(self, row: int, col: int) -> List[Tuple[int, int]]:
        """Get all valid moves for a piece at position."""
        piece = self.board[row][col]
        if piece == '.' or self._get_piece_color(piece) != self.current_player:
            return []
        
        moves = []
        color = self._get_piece_color(piece)
        p = piece.lower()
        
        if p == 'p':  # Pawn
            direction = -1 if color == 'white' else 1
            start_row = 6 if color == 'white' else 1
            
            # Forward move
            new_row = row + direction
            if self._is_valid_pos(new_row, col) and self.board[new_row][col] == '.':
                moves.append((new_row, col))
                # Double move from start
                if row == start_row:
                    new_row2 = row + 2 * direction
                    if self.board[new_row2][col] == '.':
                        moves.append((new_row2, col))
            
            # Captures
            for dc in [-1, 1]:
                new_col = col + dc
                if self._is_valid_pos(new_row, new_col):
                    target = self.board[new_row][new_col]
                    if target != '.' and self._get_piece_color(target) != color:
                        moves.append((new_row, new_col))
                    # En passant
                    if self.en_passant_target == (new_row, new_col):
                        moves.append((new_row, new_col))
        
        elif p == 'n':  # Knight
            for dr, dc in [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]:
                nr, nc = row + dr, col + dc
                if self._is_valid_pos(nr, nc):
                    target = self.board[nr][nc]
                    if target == '.' or self._get_piece_color(target) != color:
                        moves.append((nr, nc))
        
        elif p == 'r':  # Rook
            for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                for dist in range(1, 8):
                    nr, nc = row + dr*dist, col + dc*dist
                    if not self._is_valid_pos(nr, nc):
                        break
                    target = self.board[nr][nc]
                    if target == '.':
                        moves.append((nr, nc))
                    elif self._get_piece_color(target) != color:
                        moves.append((nr, nc))
                        break
                    else:
                        break
        
        elif p == 'b':  # Bishop
            for dr, dc in [(-1,-1),(-1,1),(1,-1),(1,1)]:
                for dist in range(1, 8):
                    nr, nc = row + dr*dist, col + dc*dist
                    if not self._is_valid_pos(nr, nc):
                        break
                    target = self.board[nr][nc]
                    if target == '.':
                        moves.append((nr, nc))
                    elif self._get_piece_color(target) != color:
                        moves.append((nr, nc))
                        break
                    else:
                        break
        
        elif p == 'q':  # Queen
            for dr, dc in [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)]:
                for dist in range(1, 8):
                    nr, nc = row + dr*dist, col + dc*dist
                    if not self._is_valid_pos(nr, nc):
                        break
                    target = self.board[nr][nc]
                    if target == '.':
                        moves.append((nr, nc))
                    elif self._get_piece_color(target) != color:
                        moves.append((nr, nc))
                        break
                    else:
                        break
        
        elif p == 'k':  # King
            for dr, dc in [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]:
                nr, nc = row + dr, col + dc
                if self._is_valid_pos(nr, nc):
                    target = self.board[nr][nc]
                    if target == '.' or self._get_piece_color(target) != color:
                        moves.append((nr, nc))
            
            # Castling
            if color == 'white' and row == 7 and col == 4:
                if self.castling_rights['K'] and all(self.board[7][c] == '.' for c in [5,6]) and self.board[7][7] == 'R':
                    moves.append((7, 6))
                if self.castling_rights['Q'] and all(self.board[7][c] == '.' for c in [1,2,3]) and self.board[7][0] == 'R':
                    moves.append((7, 2))
            elif color == 'black' and row == 0 and col == 4:
                if self.castling_rights['k'] and all(self.board[0][c] == '.' for c in [5,6]) and self.board[0][7] == 'r':
                    moves.append((0, 6))
                if self.castling_rights['q'] and all(self.board[0][c] == '.' for c in [1,2,3]) and self.board[0][0] == 'r':
                    moves.append((0, 2))
        
        return moves
    
    def _is_in_check(self, color: str) -> bool:
        """Check if the given color's king is in check."""
        # Find king
        king_char = 'K' if color == 'white' else 'k'
        king_pos = None
        for r in range(8):
            for c in range(8):
                if self.board[r][c] == king_char:
                    king_pos = (r, c)
                    break
            if king_pos:
                break
        
        if not king_pos:
            return False
        
        # Check if any opponent piece can capture the king
        opponent = 'black' if color == 'white' else 'white'
        for r in range(8):
            for c in range(8):
                if self.board[r][c] != '.' and self._get_piece_color(self.board[r][c]) == opponent:
                    # Temporarily change current player to get opponent's moves
                    original = self.current_player
                    self.current_player = opponent
                    moves = self._get_valid_moves_for_piece(r, c)
                    self.current_player = original
                    if king_pos in moves:
                        return True
        return False
    
    def get_all_valid_moves(self) -> List[Dict]:
        """Get all valid moves for current player, filtering out moves that leave king in check."""
        all_moves = []
        for r in range(8):
            for c in range(8):
                piece = self.board[r][c]
                if piece != '.' and self._get_piece_color(piece) == self.current_player:
                    moves = self._get_valid_moves_for_piece(r, c)
                    for mr, mc in moves:
                        # Test move
                        original = copy.deepcopy(self.board)
                        captured = self.board[mr][mc]
                        self.board[mr][mc] = piece
                        self.board[r][c] = '.'
                        
                        in_check = self._is_in_check(self.current_player)
                        
                        # Restore
                        self.board = original
                        
                        if not in_check:
                            all_moves.append({
                                "from": {"row": r, "col": c},
                                "to": {"row": mr, "col": mc},
                                "piece": piece,
                                "captured": captured if captured != '.' else None
                            })
        return all_moves
    
    def make_move(self, from_row: int, from_col: int, to_row: int, to_col: int) -> Dict:
        """Make a move and return result."""
        if self.game_over:
            return {"success": False, "error": "Game is over"}
        
        piece = self.board[from_row][from_col]
        if piece == '.' or self._get_piece_color(piece) != self.current_player:
            return {"success": False, "error": "Not your piece"}
        
        valid_moves = self.get_all_valid_moves()
        move_found = None
        for m in valid_moves:
            if m["from"]["row"] == from_row and m["from"]["col"] == from_col and \
               m["to"]["row"] == to_row and m["to"]["col"] == to_col:
                move_found = m
                break
        
        if not move_found:
            return {"success": False, "error": "Invalid move"}
        
        # Execute move
        captured = self.board[to_row][to_col]
        if captured != '.':
            if self.current_player == 'white':
                self.captured_black.append(captured)
            else:
                self.captured_white.append(captured)
        
        self.board[to_row][to_col] = piece
        self.board[from_row][from_col] = '.'
        
        # Pawn promotion
        if piece.lower() == 'p' and (to_row == 0 or to_row == 7):
            self.board[to_row][to_col] = 'Q' if self.current_player == 'white' else 'q'
        
        # Record move
        move_notation = self._algebraic_notation(from_row, from_col, to_row, to_col, piece, captured != '.')
        self.move_history.append(move_notation)
        
        # Switch player
        self.current_player = 'black' if self.current_player == 'white' else 'white'
        
        # Check game state
        if not self.get_all_valid_moves():
            if self._is_in_check(self.current_player):
                self.game_over = True
                self.winner = 'white' if self.current_player == 'black' else 'black'
            else:
                self.game_over = True
                self.draw = True
        
        return {
            "success": True,
            "move": move_notation,
            "captured": captured if captured != '.' else None,
            "game_over": self.game_over,
            "board": self.get_board_state()
        }
    
    def ai_move(self) -> Dict:
        """Sarah makes a move using minimax."""
        if self.game_over or self.current_player != 'black':
            return {"success": False, "error": "Not AI's turn"}
        
        moves = self.get_all_valid_moves()
        if not moves:
            return {"success": False, "error": "No valid moves"}
        
        # Simple evaluation with minimax depth 2
        best_move = None
        best_score = -99999
        
        for move in moves:
            # Make move
            piece = self.board[move["from"]["row"]][move["from"]["col"]]
            captured = self.board[move["to"]["row"]][move["to"]["col"]]
            self.board[move["to"]["row"]][move["to"]["col"]] = piece
            self.board[move["from"]["row"]][move["from"]["col"]] = '.'
            
            score = -self._minimax(1, -99999, 99999, False)
            
            # Undo
            self.board[move["from"]["row"]][move["from"]["col"]] = piece
            self.board[move["to"]["row"]][move["to"]["col"]] = captured
            
            if score > best_score:
                best_score = score
                best_move = move
        
        if best_move:
            result = self.make_move(best_move["from"]["row"], best_move["from"]["col"],
                                  best_move["to"]["row"], best_move["to"]["col"])
            result["ai_thought"] = f"I evaluated {len(moves)} moves and chose the best one!"
            return result
        
        return {"success": False, "error": "AI could not find a move"}
    
    def _minimax(self, depth: int, alpha: int, beta: int, is_maximizing: bool) -> int:
        """Minimax with alpha-beta pruning."""
        if depth == 0:
            return self._evaluate_board()
        
        moves = self.get_all_valid_moves()
        if not moves:
            if self._is_in_check(self.current_player):
                return -9000 if is_maximizing else 9000
            return 0
        
        if is_maximizing:
            max_eval = -99999
            for move in moves:
                piece = self.board[move["from"]["row"]][move["from"]["col"]]
                captured = self.board[move["to"]["row"]][move["to"]["col"]]
                self.board[move["to"]["row"]][move["to"]["col"]] = piece
                self.board[move["from"]["row"]][move["from"]["col"]] = '.'
                self.current_player = 'white' if self.current_player == 'black' else 'black'
                
                eval = self._minimax(depth - 1, alpha, beta, False)
                
                self.current_player = 'white' if self.current_player == 'black' else 'black'
                self.board[move["from"]["row"]][move["from"]["col"]] = piece
                self.board[move["to"]["row"]][move["to"]["col"]] = captured
                
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = 99999
            for move in moves:
                piece = self.board[move["from"]["row"]][move["from"]["col"]]
                captured = self.board[move["to"]["row"]][move["to"]["col"]]
                self.board[move["to"]["row"]][move["to"]["col"]] = piece
                self.board[move["from"]["row"]][move["from"]["col"]] = '.'
                self.current_player = 'white' if self.current_player == 'black' else 'black'
                
                eval = self._minimax(depth - 1, alpha, beta, True)
                
                self.current_player = 'white' if self.current_player == 'black' else 'black'
                self.board[move["from"]["row"]][move["from"]["col"]] = piece
                self.board[move["to"]["row"]][move["to"]["col"]] = captured
                
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha:
                    break
            return min_eval
    
    def _evaluate_board(self) -> int:
        """Evaluate board position. Positive = good for black (Sarah)."""
        values = {'p': 100, 'n': 320, 'b': 330, 'r': 500, 'q': 900, 'k': 20000}
        score = 0
        for r in range(8):
            for c in range(8):
                piece = self.board[r][c]
                if piece != '.':
                    val = values.get(piece.lower(), 0)
                    if piece.isupper():
                        score -= val
                    else:
                        score += val
        return score
    
    def _algebraic_notation(self, fr, fc, tr, tc, piece, is_capture) -> str:
        """Convert move to algebraic notation."""
        files = 'abcdefgh'
        ranks = '87654321'
        p = piece.upper()
        if p == 'P':
            if is_capture:
                return f"{files[fc]}x{files[tc]}{ranks[tr]}"
            return f"{files[tc]}{ranks[tr]}"
        capture = "x" if is_capture else ""
        return f"{p}{capture}{files[tc]}{ranks[tr]}"
    
    def save_game(self):
        """Save game to history."""
        game_data = {
            "date": datetime.now().isoformat(),
            "moves": self.move_history,
            "winner": self.winner,
            "draw": self.draw
        }
        self.game_history.append(game_data)
        with open(self.save_file, 'w') as f:
            json.dump(self.game_history, f)

# Plugin interface
class Plugin:
    def __init__(self):
        self.game = ChessGame()
    
    def get_info(self) -> Dict:
        return self.game.get_info()
    
    def new_game(self) -> Dict:
        self.game.reset_game()
        return self.game.get_board_state()
    
    def make_move(self, from_row: int, from_col: int, to_row: int, to_col: int) -> Dict:
        result = self.game.make_move(from_row, from_col, to_row, to_col)
        if result.get("success") and not result.get("game_over") and self.game.current_player == 'black':
            ai_result = self.game.ai_move()
            return {"player_move": result, "ai_move": ai_result, "board": self.game.get_board_state()}
        return {"player_move": result, "board": self.game.get_board_state()}
    
    def get_board(self) -> Dict:
        return self.game.get_board_state()
