# core/license_crypto.py
from __future__ import annotations

import base64
import json
import hashlib
from typing import Any

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from core.license_public_key import PUBLIC_KEY_PEM


def b64encode_json(data: dict[str, Any]) -> str:
    raw = json.dumps(data, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return base64.b64encode(raw).decode("utf-8")


def b64decode_json(payload_b64: str) -> dict[str, Any]:
    raw = base64.b64decode(payload_b64.encode("utf-8"))
    return json.loads(raw.decode("utf-8"))


def _load_public_key() -> Ed25519PublicKey:
    pub = serialization.load_pem_public_key(PUBLIC_KEY_PEM)
    if not isinstance(pub, Ed25519PublicKey):
        raise TypeError("Public key is not Ed25519")
    return pub


def verify_signature(payload_b64: str, signature_b64: str) -> bool:
    try:
        pub = _load_public_key()
        sig = base64.b64decode(signature_b64.encode("utf-8"))
        pub.verify(sig, payload_b64.encode("utf-8"))
        return True
    except Exception:
        return False


def sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()
