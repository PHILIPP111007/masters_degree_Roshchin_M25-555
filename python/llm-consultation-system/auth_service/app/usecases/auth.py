from app.core.exceptions import (
    InvalidCredentialsError,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from app.core.security import create_access_token, hash_password, verify_password
from app.repositories.users import UserRepository
from app.schemas.user import UserPublic


class AuthUseCase:
    def __init__(self, user_repo: UserRepository):
        self._user_repo = user_repo

    async def register(self, email: str, password: str) -> UserPublic:
        existing = await self._user_repo.get_by_email(email)
        if existing:
            raise UserAlreadyExistsError(meta={"email": email})

        hashed = hash_password(password)
        user = await self._user_repo.create(email=email, password_hash=hashed)
        return UserPublic.model_validate(user)

    async def login(self, email: str, password: str) -> str:
        user = await self._user_repo.get_by_email(email)
        if not user:
            raise InvalidCredentialsError()

        if not verify_password(password, user.password_hash):
            raise InvalidCredentialsError()

        return create_access_token(user_id=user.id, role=user.role)

    async def me(self, user_id: int) -> UserPublic:
        user = await self._user_repo.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(meta={"user_id": user_id})
        return UserPublic.model_validate(user)
