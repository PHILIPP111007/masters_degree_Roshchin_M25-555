import time

from jose import jwt

from app.core.config import settings
from app.core.jwt import decode_and_validate


def test_decode_valid_token():
    token = jwt.encode(
        {"sub": "42", "role": "user", "exp": int(time.time()) + 3600},
        settings.jwt_secret,
        algorithm=settings.jwt_alg,
    )
    payload = decode_and_validate(token)
    assert payload["sub"] == "42"
    assert payload["role"] == "user"


def test_decode_invalid_token():
    try:
        decode_and_validate("garbage.token.here")
        assert False, "Should have raised ValueError"
    except ValueError:
        pass
