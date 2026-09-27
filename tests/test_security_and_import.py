from mathblitz.core.security import PasswordHasher, TokenService
from mathblitz.db.legacy_import import normalized_difficulty


def test_password_hash_is_salted_and_verifiable() -> None:
    hasher = PasswordHasher()
    first = hasher.hash("correct horse battery staple")
    second = hasher.hash("correct horse battery staple")
    assert first != second
    assert hasher.verify("correct horse battery staple", first).valid
    assert not hasher.verify("incorrect", first).valid


def test_tokens_expire_or_verify_subject() -> None:
    service = TokenService("secret", 10)
    token, _ = service.issue("user-123")
    assert service.subject(token) == "user-123"
    assert service.subject(f"{token}invalid") is None


def test_legacy_level_name_is_translated() -> None:
    assert normalized_difficulty("Very Hard") == "Extreme Hard"
    assert normalized_difficulty("Medium") == "Medium"
