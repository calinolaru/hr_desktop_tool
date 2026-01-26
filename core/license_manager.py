# core/license_manager.py
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from core.license_crypto import b64decode_json, verify_signature
from core.machine_fingerprint import get_machine_fingerprint
from core.paths import resource_path


class LicenseError(Exception):
    pass


@dataclass(frozen=True)
class LicenseInfo:
    license_type: str  # "trial" | "full"
    company: str
    vat: str
    machine: str
    issued_at: str
    expires: Optional[str] = None


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_iso(dt: str) -> datetime:
    # Expect ISO like: 2026-01-25T12:00:00+00:00
    return datetime.fromisoformat(dt)


def _license_file_path() -> Path:
    # user drops it next to app in ./config/license.json
    return resource_path("config/license.json")


def load_and_validate_license() -> LicenseInfo:
    path = _license_file_path()

    if not path.exists():
        raise LicenseError(
            "Lipsă licență.\n\n"
            "Copiază fișierul config/license.json în folderul aplicației.\n"
            "Dacă ai nevoie de Trial / licență nouă, trimite Machine ID la furnizor."
        )

    # --- load JSON ---
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        raise LicenseError("Fișierul license.json este invalid (nu este JSON).")

    payload_b64 = str(raw.get("payload", "")).strip()
    signature_b64 = str(raw.get("signature", "")).strip()

    if not payload_b64 or not signature_b64:
        raise LicenseError(
            "Fișierul license.json este incomplet "
            "(lipsește payload și/sau signature)."
        )

    # --- cryptographic verification ---
    if not verify_signature(payload_b64, signature_b64):
        raise LicenseError("Licență invalidă (semnătură greșită).")

    # --- decode payload ---
    try:
        data = b64decode_json(payload_b64)
    except Exception:
        raise LicenseError("Licență invalidă (payload base64 corupt).")

    # --- required fields ---
    required_fields = ("type", "company", "vat", "machine", "issued_at")
    for k in required_fields:
        if k not in data or not str(data[k]).strip():
            raise LicenseError(f"Licență invalidă (lipsește câmpul: {k}).")

    lic_type = str(data["type"]).strip().lower()
    if lic_type not in ("trial", "full"):
        raise LicenseError("Licență invalidă (type trebuie trial sau full).")

    # --- PC binding ---
    expected_machine = str(data["machine"]).strip()
    actual_machine = get_machine_fingerprint()

    if expected_machine != actual_machine:
        raise LicenseError(
            "Licența nu este pentru acest PC.\n\n"
            f"Machine ID curent:\n{actual_machine}\n\n"
            "Trimite acest Machine ID furnizorului pentru o licență compatibilă."
        )

    # --- expiry check (trial only) ---
    expires = data.get("expires")
    if expires:
        try:
            exp_dt = _parse_iso(str(expires))
        except Exception:
            raise LicenseError("Licență invalidă (expires nu este ISO datetime).")

        if _utc_now() > exp_dt:
            raise LicenseError(
                "Licența Trial a expirat.\n"
                "Contactează furnizorul pentru activare."
            )

    # --- OK ---
    return LicenseInfo(
        license_type=lic_type,
        company=str(data["company"]).strip(),
        vat=str(data["vat"]).strip(),
        machine=expected_machine,
        issued_at=str(data["issued_at"]).strip(),
        expires=str(expires).strip() if expires else None,
    )

