from __future__ import annotations

from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken


class CryptoError(Exception):
    """Raised when encryption/decryption fails."""


def ensure_key(key_path: Path) -> bytes:
    """Load or create a Fernet key at ``key_path``."""
    key_path.parent.mkdir(parents=True, exist_ok=True)
    if key_path.exists():
        return key_path.read_bytes().strip()
    key = Fernet.generate_key()
    key_path.write_bytes(key)
    try:
        key_path.chmod(0o600)
    except OSError:
        # Windows may not support POSIX mode bits; ignore.
        pass
    return key


class CredentialCrypto:
    """Encrypt/decrypt credential strings with Fernet."""

    def __init__(self, key: bytes) -> None:
        self._fernet = Fernet(key)

    @classmethod
    def from_path(cls, key_path: Path) -> CredentialCrypto:
        return cls(ensure_key(key_path))

    def encrypt(self, plaintext: str) -> str:
        return self._fernet.encrypt(plaintext.encode("utf-8")).decode("ascii")

    def decrypt(self, token: str) -> str:
        try:
            return self._fernet.decrypt(token.encode("ascii")).decode("utf-8")
        except (InvalidToken, ValueError) as exc:
            raise CryptoError("Failed to decrypt credential") from exc
