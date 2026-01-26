# tools/gen_keys.py
from __future__ import annotations

from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

KEYS_DIR = Path("keys")
PRIV_PATH = KEYS_DIR / "private_key.pem"
PUB_PATH = KEYS_DIR / "public_key.pem"


def main() -> None:
    KEYS_DIR.mkdir(parents=True, exist_ok=True)

    priv = Ed25519PrivateKey.generate()
    pub = priv.public_key()

    priv_pem = priv.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),  # poți pune parolă mai târziu
    )
    pub_pem = pub.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    PRIV_PATH.write_bytes(priv_pem)
    PUB_PATH.write_bytes(pub_pem)

    print("Generated:")
    print(f"  Private: {PRIV_PATH.resolve()}")
    print(f"  Public : {PUB_PATH.resolve()}")
    print("\nIMPORTANT:")
    print("- NU trimite private_key.pem la nimeni.")
    print("- public_key.pem îl folosește aplicația pentru verificare.")


if __name__ == "__main__":
    main()
