# core/trial_guard.py
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import json
import sys


class TimeRollbackError(ValueError):
    pass


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _guard_file_path() -> Path:
    """
    Fișier local unde ținem ultima dată validă cunoscută.
    Este local, nu criptat, dar suficient pentru descurajare.
    """
    if getattr(sys, "frozen", False):
        base = Path(sys.executable).resolve().parent
    else:
        base = Path(__file__).resolve().parents[1]

    return base / "config" / ".trial_guard.json"


def enforce_no_time_rollback() -> None:
    """
    Blochează rularea dacă ceasul sistemului a fost dat înapoi
    față de ultima rulare validă.
    """
    now = _utc_now()
    path = _guard_file_path()
    path.parent.mkdir(exist_ok=True)

    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            last_seen = datetime.fromisoformat(data.get("last_seen"))
        except Exception:
            last_seen = None

        if last_seen and now < last_seen:
            raise TimeRollbackError(
                "Data sistemului pare modificată.\n\n"
                "Te rugăm să setezi data și ora corecte pe calculator "
                "și să repornești aplicația."
            )

    # update last seen timestamp
    path.write_text(
        json.dumps({"last_seen": now.isoformat()}),
        encoding="utf-8"
    )
