import sys
import os
import types

# Stub pygame if not installed
sys.modules.setdefault('pygame', types.ModuleType('pygame'))
# Ensure repository root is on path
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

def test_import():
    import mahjong_game
    assert hasattr(mahjong_game, 'MahjongGame')

