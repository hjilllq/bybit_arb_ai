import tempfile, pathlib, sys
from decimal import Decimal
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from state_persistence import load_state, save_state
import config


def test_load_from_backup(monkeypatch):
    with tempfile.TemporaryDirectory() as td:
        path = pathlib.Path(td) / "state.json"
        backup = pathlib.Path(td) / "state.bak.json"
        # write corrupted main file
        path.write_text("{bad json}")
        state = {
            "position": {"BTCUSDT": Decimal("1")},
            "entry": {"BTCUSDT": Decimal("100")},
            "real": {"BTCUSDT": Decimal("5")},
            "unreal": {"BTCUSDT": Decimal("-2")},
        }
        save_state(state, backup)
        monkeypatch.setattr(config, "STATE_FILE", path)
        monkeypatch.setattr(config, "STATE_BACKUP_FILE", backup)
        loaded = load_state()
        assert loaded == state
