# tools/license_gen.py
from __future__ import annotations

import argparse
import base64
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from core.license_crypto import b64encode_json


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_license_payload(
    lic_type: str,
    company: str,
    vat: str,
    machine: str,
    days: int | None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "type": lic_type,
        "company": company.strip(),
        "vat": vat.strip(),
        "machine": machine.strip(),
        "issued_at": utc_now_iso(),
    }
    if lic_type == "trial":
        d = days or 7
        payload["expires"] = (datetime.now(timezone.utc) + timedelta(days=d)).isoformat()
    return payload


def load_private_key(path: Path) -> Ed25519PrivateKey:
    data = path.read_bytes()
    k = serialization.load_pem_private_key(data, password=None)
    if not isinstance(k, Ed25519PrivateKey):
        raise TypeError("Private key is not Ed25519")
    return k


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--type", choices=["trial", "full"], required=True)
    ap.add_argument("--company", required=True)
    ap.add_argument("--vat", required=True)
    ap.add_argument("--machine", required=True)
    ap.add_argument("--days", type=int, default=7)
    ap.add_argument("--out", default="config/license.json")
    ap.add_argument("--private-key", default="keys/private_key.pem")
    args = ap.parse_args()

    priv_path = Path(args.private_key)
    if not priv_path.exists():
        raise SystemExit(f"Missing private key: {priv_path}")

    priv = load_private_key(priv_path)

    payload_dict = make_license_payload(args.type, args.company, args.vat, args.machine, args.days)
    payload_b64 = b64encode_json(payload_dict)

    sig_bytes = priv.sign(payload_b64.encode("utf-8"))
    sig_b64 = base64.b64encode(sig_bytes).decode("utf-8")

    out_obj = {"payload": payload_b64, "signature": sig_b64}

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out_obj, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Saved license: {out_path.resolve()}")


if __name__ == "__main__":
    main()
