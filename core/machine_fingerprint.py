# core/machine_fingerprint.py
from __future__ import annotations

import os
import platform
import subprocess

from core.license_crypto import sha256_hex


def _run(cmd: list[str]) -> str:
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.DEVNULL, text=True, encoding="utf-8")
        return out.strip()
    except Exception:
        return ""


def _windows_machine_guid() -> str:
    """
    Stable on Windows installs:
    HKLM\\SOFTWARE\\Microsoft\\Cryptography\\MachineGuid
    """
    if platform.system().lower() != "windows":
        return ""
    out = _run(["reg", "query", r"HKLM\SOFTWARE\Microsoft\Cryptography", "/v", "MachineGuid"])
    # output format includes the GUID as last token
    if not out:
        return ""
    parts = out.split()
    return parts[-1].strip() if parts else ""


def _wmic_uuid() -> str:
    """Sometimes available; can fail on newer Windows."""
    if platform.system().lower() != "windows":
        return ""
    out = _run(["wmic", "csproduct", "get", "uuid"])
    lines = [l.strip() for l in out.splitlines() if l.strip()]
    if len(lines) >= 2:
        return lines[1]
    return ""


def get_machine_fingerprint() -> str:
    """
    Returns a stable-ish fingerprint hash.
    Primary: MachineGuid.
    Fallback: wmic uuid.
    Final fallback: hostname+platform (weak).
    """
    mg = _windows_machine_guid()
    if mg:
        return sha256_hex(f"MG:{mg}")

    uuid = _wmic_uuid()
    if uuid:
        return sha256_hex(f"UUID:{uuid}")

    # weak fallback (should rarely be used on Windows)
    host = os.environ.get("COMPUTERNAME", "") or platform.node()
    sys = platform.platform()
    return sha256_hex(f"FALLBACK:{host}|{sys}")
