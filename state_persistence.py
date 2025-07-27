from __future__ import annotations
import json
from decimal import Decimal
from pathlib import Path
import config


def load_state(path: Path | None = None) -> dict:
    """Load persisted trading state from JSON."""
    path = path or config.STATE_FILE
    if not path.exists():
        return {}
    try:
        with path.open() as f:
            data = json.load(f)
    except Exception:
        if config.STATE_BACKUP_FILE.exists():
            with config.STATE_BACKUP_FILE.open() as f:
                data = json.load(f)
        else:
            return {}
    for dkey in ("position", "real", "unreal"):
        if dkey in data:
            data[dkey] = {k: Decimal(v) for k, v in data[dkey].items()}
    if "entry" in data:
        data["entry"] = {k: Decimal(v) if v is not None else None for k, v in data["entry"].items()}
    if "high_water" in data:
        data["high_water"] = Decimal(data["high_water"])
    if "sym_high_water" in data:
        data["sym_high_water"] = {k: Decimal(v) for k, v in data["sym_high_water"].items()}
    return data


def save_state(state: dict, path: Path | None = None) -> None:
    """Persist trading state to JSON."""
    path = path or config.STATE_FILE
    payload = {}
    for key in ("position", "real", "unreal", "entry", "high_water", "sym_high_water"):
        if key in state:
            val = state[key]
            if key == "entry":
                payload[key] = {k: (str(v) if v is not None else None) for k, v in val.items()}
            elif key == "sym_high_water":
                payload[key] = {k: str(v) for k, v in val.items()}
            elif key == "high_water":
                payload[key] = str(val)
            else:
                payload[key] = {k: str(v) for k, v in val.items()}
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(payload))
    if path.exists():
        path.replace(config.STATE_BACKUP_FILE)
    tmp.replace(path)
