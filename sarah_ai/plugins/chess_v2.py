import json
import os
import uuid
from datetime import datetime
from typing import Dict, Any

# Attempt to reuse the existing chess_game implementation for core rules/AI
try:
    import importlib.util
    base_dir = os.path.dirname(__file__)
    chess_path = os.path.join(base_dir, "chess_game.py")
    if os.path.exists(chess_path):
        spec = importlib.util.spec_from_file_location("chess_game", chess_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        chess_game = module
    else:
        chess_game = None
except Exception:
    chess_game = None


class ChessManagerV2:
    """Wrapper around existing ChessGame with match history, difficulty/ELO, and persistence."""

    def __init__(self, save_file: str = "memory/chess_v2.json"):
        self.save_file = save_file
        os.makedirs(os.path.dirname(self.save_file) or "memory", exist_ok=True)
        self.history = self._load_history()
        # underlying game (fallback to original implementation)
        self.game = chess_game.ChessGame() if chess_game else None
        self.current_match: Dict[str, Any] = {}
        # Stats per difficulty
        self.stats_file = "memory/chess_v2_stats.json"
        self.stats = self._load_stats()
        # Player rating (ELO)
        self.player_rating = self.stats.get("player_rating", 1200)
        self.stats.setdefault("rating_history", [])

    def _load_history(self):
        if os.path.exists(self.save_file):
            try:
                with open(self.save_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def _save_history(self):
        try:
            with open(self.save_file, "w", encoding="utf-8") as f:
                json.dump(self.history, f, indent=2)
        except Exception:
            pass

    def _load_stats(self):
        if os.path.exists(self.stats_file):
            try:
                with open(self.stats_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_stats(self):
        try:
            with open(self.stats_file, "w", encoding="utf-8") as f:
                json.dump(self.stats, f, indent=2)
        except Exception:
            pass

    def new_game(self, difficulty: str = "normal") -> Dict[str, Any]:
        # Reset or create underlying game
        if self.game:
            self.game.reset_game()
            # Map difficulty to approximate elo
            mapping = {"easy": 900, "normal": 1400, "hard": 2000, "master": 2600}
            self.game.set_ai_level(mapping.get(difficulty, 1400))

        self.current_match = {
            "id": str(uuid.uuid4()),
            "started": datetime.now().isoformat(),
            "difficulty": difficulty,
            "moves": [],
            "winner": None,
            "draw": False,
        }
        return self.get_board()

    def get_board(self) -> Dict[str, Any]:
        if self.game:
            board_state = self.game.get_board_state()
            board_state["difficulty"] = self.current_match.get("difficulty", "normal")
            board_state["player_rating"] = self.player_rating
            board_state["match_id"] = self.current_match.get("id")
            board_state["chess_stats"] = self.stats
            return board_state
        return {"success": False, "error": "No game implementation available"}

    def make_move(self, from_row: int, from_col: int, to_row: int, to_col: int, auto_ai: bool = True) -> Dict[str, Any]:
        if not self.game:
            return {"success": False, "error": "No game implementation available"}

        player_result = self.game.make_move(from_row, from_col, to_row, to_col)

        ai_result = None
        try:
            # If configured, let the engine make its move immediately
            if auto_ai and isinstance(player_result, dict) and player_result.get("success") and not player_result.get("game_over") and getattr(self.game, "current_player", "") == 'black':
                ai_result = self.game.ai_move()

            # Record moves in current match
            try:
                # Player move
                if isinstance(player_result, dict):
                    mv = player_result.get("move")
                    if mv:
                        self.current_match.setdefault("moves", []).append(mv)
                # AI move
                if ai_result and isinstance(ai_result, dict):
                    mv2 = ai_result.get("move")
                    if mv2:
                        self.current_match.setdefault("moves", []).append(mv2)
            except Exception:
                pass

            # Determine game over state and winner (check both player_result and ai_result and underlying game)
            game_over = False
            winner = None
            draw = False
            if isinstance(player_result, dict) and player_result.get("game_over"):
                game_over = True
                winner = player_result.get("winner")
            if isinstance(ai_result, dict) and ai_result.get("game_over"):
                game_over = True
                winner = ai_result.get("winner")
            if hasattr(self.game, "game_over") and getattr(self.game, "game_over"):
                game_over = True
                winner = getattr(self.game, "winner", None)
                draw = getattr(self.game, "draw", False)

            if game_over:
                self.current_match["ended"] = datetime.now().isoformat()
                self.current_match["winner"] = winner
                self.current_match["draw"] = draw
                self.history.append(self.current_match)
                self._save_history()

                # Update stats
                try:
                    diff = self.current_match.get("difficulty", "normal")
                    s = self.stats.setdefault(diff, {"wins": 0, "losses": 0, "draws": 0, "played": 0})
                    s["played"] = s.get("played", 0) + 1
                    if draw:
                        s["draws"] = s.get("draws", 0) + 1
                    else:
                        if winner == 'white':
                            s["wins"] = s.get("wins", 0) + 1
                        else:
                            s["losses"] = s.get("losses", 0) + 1

                    # ELO update against AI's level
                    try:
                        k = 32
                        ai_elo = getattr(self.game, 'ai_level', None) or 1400
                        if draw:
                            s_score = 0.5
                        else:
                            s_score = 1.0 if winner == 'white' else 0.0
                        expected = 1.0 / (1.0 + 10 ** ((ai_elo - self.player_rating) / 400.0))
                        new_rating = int(round(self.player_rating + k * (s_score - expected)))
                        self.stats.setdefault("rating_history", []).append({
                            "time": datetime.now().isoformat(),
                            "before": self.player_rating,
                            "after": new_rating,
                            "opponent_elo": ai_elo,
                            "result": s_score,
                        })
                        self.player_rating = new_rating
                        self.stats["player_rating"] = self.player_rating
                    except Exception:
                        pass
                    self._save_stats()
                except Exception:
                    pass

        except Exception:
            pass

        # Return wrapper compatible with older plugin API
        wrapper: Dict[str, Any] = {"player_move": player_result, "board": self.game.get_board_state()}
        if ai_result:
            wrapper["ai_move"] = ai_result

        return wrapper

    def export_pgn(self, match_id: str = None) -> str:
        """Export a simple PGN-like string for a finished match or current match.

        This produces a minimal, human-readable move list (numbered moves).
        """
        match = None
        if match_id:
            for m in self.history:
                if m.get("id") == match_id:
                    match = m
                    break
        else:
            match = self.current_match if self.current_match else (self.history[-1] if self.history else None)

        if not match:
            return ""

        moves = match.get("moves", [])
        parts = []
        for i in range(0, len(moves), 2):
            num = i // 2 + 1
            white = moves[i]
            black = moves[i + 1] if i + 1 < len(moves) else ""
            if black:
                parts.append(f"{num}. {white} {black}")
            else:
                parts.append(f"{num}. {white}")

        return " ".join(parts)


class Plugin:
    def __init__(self):
        self.manager = ChessManagerV2()

    def get_info(self) -> Dict[str, str]:
        return {"name": "Chess v2", "description": "Enhanced chess with match history & ELO", "version": "0.1"}

    def new_game(self, difficulty: str = "normal") -> Dict[str, Any]:
        return self.manager.new_game(difficulty)

    def get_board(self) -> Dict[str, Any]:
        return self.manager.get_board()

    def make_move(self, from_row: int, from_col: int, to_row: int, to_col: int, auto_ai: bool = True) -> Dict[str, Any]:
        # Keep compatibility: forward auto_ai to manager
        return self.manager.make_move(from_row, from_col, to_row, to_col, auto_ai=auto_ai)

    def get_history(self) -> Dict[str, Any]:
        return {"history": self.manager.history}

    def get_stats(self) -> Dict[str, Any]:
        return {"stats": self.manager.stats}

    def export_pgn(self, match_id: str = None) -> str:
        return self.manager.export_pgn(match_id)
