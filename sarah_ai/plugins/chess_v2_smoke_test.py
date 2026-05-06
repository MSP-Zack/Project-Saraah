import time

print('Loading chess_v2 plugin smoke test')
try:
    from chess_v2 import Plugin
except Exception as e:
    print('Import failed:', e)
    raise

pl = Plugin()
print('Plugin info:', pl.get_info())

print('Starting new game...')
board = pl.new_game('normal')
print('Board state keys:', list(board.keys()))

print('Making sample move: pawn a2 to a4 (6,0 -> 4,0)')
res = pl.make_move(6, 0, 4, 0)
print('Move result:', res)

try:
    pgn = pl.manager.export_pgn()
    print('Exported PGN:', pgn)
except Exception as e:
    print('PGN export failed:', e)

print('Smoke test completed')
print('Stats:', pl.get_stats())
