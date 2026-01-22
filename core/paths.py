from __future__ import annotations
from pathlib import Path
import sys

def resource_path(rel: str) -> Path:
    """
    Returnează path corect atât din source, cât și din PyInstaller bundle.
    """
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        base = Path(sys._MEIPASS)  # type: ignore[attr-defined]
    else:
        base = Path(__file__).resolve().parent.parent  # root proiect
    return base / rel
