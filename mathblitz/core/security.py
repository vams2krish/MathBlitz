"""Password hashing and signed access-token services."""

from dataclasses import dataclass
import base64
import hashlib
import hmac
import json
import secrets
import time


@dataclass(frozen=True)
class PasswordVerification:
    valid: bool
    requires_upgrade: bool = False


class PasswordHasher:
    """Hashes passwords using scrypt and verifies legacy application hashes."""

    algorithm = "scrypt"

    def hash(self, password: str) -> str:
        salt = secrets.token_bytes(16)
        digest = hashlib.scrypt(
            password.encode("utf-8"), salt=salt, n=2**14, r=8, p=1, dklen=32
        )
        return "$".join(
            (
                self.algorithm,
                base64.urlsafe_b64encode(salt).decode("ascii"),
                base64.urlsafe_b64encode(digest).decode("ascii"),
            )
        )

    def verify(self, password: str, stored_hash: str) -> PasswordVerification:
        if stored_hash.startswith(f"{self.algorithm}$"):
            try:
                _, salt_text, expected_text = stored_hash.split("$", maxsplit=2)
                salt = base64.urlsafe_b64decode(salt_text.encode("ascii"))
                expected = base64.urlsafe_b64decode(expected_text.encode("ascii"))
                actual = hashlib.scrypt(
                    password.encode("utf-8"),
                    salt=salt,
                    n=2**14,
                    r=8,
                    p=1,
                    dklen=32,
                )
                return PasswordVerification(hmac.compare_digest(actual, expected))
            except (ValueError, TypeError):
                return PasswordVerification(False)

        if "$" in stored_hash:
            try:
                salt, expected = stored_hash.split("$", maxsplit=1)
                actual = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
                valid = hmac.compare_digest(actual, expected)
                return PasswordVerification(valid, valid)
            except ValueError:
                return PasswordVerification(False)

        valid = hmac.compare_digest(password, stored_hash)
        return PasswordVerification(valid, valid)


class TokenService:
    """Issues compact HMAC-signed bearer tokens without storing server sessions."""

    def __init__(self, secret_key: str, ttl_minutes: int) -> None:
        self._key = secret_key.encode("utf-8")
        self._ttl_seconds = ttl_minutes * 60

    @staticmethod
    def _encode(raw: bytes) -> str:
        return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")

    @staticmethod
    def _decode(encoded: str) -> bytes:
        padding = "=" * (-len(encoded) % 4)
        return base64.urlsafe_b64decode((encoded + padding).encode("ascii"))

    def issue(self, user_id: str) -> tuple[str, int]:
        expires_at = int(time.time()) + self._ttl_seconds
        payload = self._encode(
            json.dumps(
                {"sub": user_id, "exp": expires_at},
                separators=(",", ":"),
            ).encode("utf-8")
        )
        signature = self._encode(
            hmac.new(self._key, payload.encode("ascii"), hashlib.sha256).digest()
        )
        return f"{payload}.{signature}", expires_at

    def subject(self, token: str) -> str | None:
        try:
            payload, signature = token.split(".", maxsplit=1)
            expected = self._encode(
                hmac.new(self._key, payload.encode("ascii"), hashlib.sha256).digest()
            )
            if not hmac.compare_digest(signature, expected):
                return None
            claims = json.loads(self._decode(payload).decode("utf-8"))
            if int(claims["exp"]) <= int(time.time()):
                return None
            return str(claims["sub"])
        except (ValueError, KeyError, TypeError, json.JSONDecodeError):
            return None
