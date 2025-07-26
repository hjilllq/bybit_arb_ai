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
    with path.open() as f:
        data = json.load(f)
    for dkey in ("position", "real", "unreal"):
        if dkey in data:
            data[dkey] = {k: Decimal(v) for k, v in data[dkey].items()}
    if "entry" in data:
        data["entry"] = {k: Decimal(v) if v is not None else None for k, v in data["entry"].items()}
    return data


def save_state(state: dict, path: Path | None = None) -> None:
    """Persist trading state to JSON."""
    path = path or config.STATE_FILE
    payload = {}
    for key in ("position", "real", "unreal", "entry"):
        if key in state:
            val = state[key]
            if key == "entry":
                payload[key] = {k: (str(v) if v is not None else None) for k, v in val.items()}
            else:
                payload[key] = {k: str(v) for k, v in val.items()}
    path.write_text(json.dumps(payload))
