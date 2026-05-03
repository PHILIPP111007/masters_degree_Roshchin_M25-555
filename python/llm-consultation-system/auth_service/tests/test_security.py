from app.core.security import (
    create_access_token,
    decode_token,
    hash_password,
    verify_password,
)


def test_hash_and_verify_password():
    password = "secret123"
    hashed = hash_password(password)

    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("wrong", hashed) is False


def test_create_and_decode_token():
    token = create_access_token(user_id=42, role="admin")
    payload = decode_token(token)

    assert payload["sub"] == "42"
    assert payload["role"] == "admin"
    assert "iat" in payload
    assert "exp" in payload


def test_decode_invalid_token():
    try:
        decode_token("invalid.token.here")
        assert False, "Should have raised ValueError"
    except ValueError:
        pass
