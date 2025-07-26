import tempfile, json
from decimal import Decimal
import sys, pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from state_persistence import load_state, save_state


def test_save_and_load_roundtrip():
    with tempfile.TemporaryDirectory() as td:
        path = pathlib.Path(td) / "state.json"
        state = {
            "position": {"BTCUSDT": Decimal("1")},
            "entry": {"BTCUSDT": Decimal("100")},
            "real": {"BTCUSDT": Decimal("5")},
            "unreal": {"BTCUSDT": Decimal("-2")},
        }
        save_state(state, path)
        loaded = load_state(path)
        assert loaded == state
