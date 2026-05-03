from jose import JWTError, jwt

from app.core.config import settings


def decode_and_validate(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_alg])
        if "sub" not in payload:
            raise ValueError("Token missing 'sub' field")
        return payload
    except JWTError:
        raise ValueError("Invalid or expired token")
