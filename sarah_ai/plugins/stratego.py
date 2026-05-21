import importlib.util
import os

base_dir = os.path.dirname(__file__)
stratego_v2_path = os.path.join(base_dir, 'stratego_v2', 'plugin.py')
StrategoPlugin = None
if os.path.exists(stratego_v2_path):
    spec = importlib.util.spec_from_file_location('stratego_v2.plugin', stratego_v2_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    StrategoPlugin = getattr(module, 'StrategoPlugin', None)

class Plugin:
    def __init__(self):
        if not StrategoPlugin:
            raise ImportError('Stratego v2 plugin could not be loaded')
        self.instance = StrategoPlugin()

    def get_info(self):
        return self.instance.get_info()

    def new_game(self, difficulty=3, preset='classic', rows=None, columns=None, piece_counts=None, manual_setup=True, obstacles=None):
        return self.instance.new_game(
            difficulty,
            preset=preset,
            rows=rows,
            columns=columns,
            piece_counts=piece_counts,
            manual_setup=manual_setup,
            obstacles=obstacles,
        )

    def get_board(self):
        return self.instance.get_board()

    def make_move(self, from_row, from_col, to_row, to_col, auto_ai=True):
        return self.instance.make_move(from_row, from_col, to_row, to_col, auto_ai=auto_ai)

    def place_piece(self, row, col, code):
        return self.instance.place_piece(row, col, code)

    def remove_piece(self, row, col):
        return self.instance.remove_piece(row, col)

    def begin_game(self):
        return self.instance.begin_game()

    def save_game(self):
        return self.instance.save_game()

    def load_game(self):
        return self.instance.load_game()

    def get_stats(self):
        return self.instance.get_stats()
