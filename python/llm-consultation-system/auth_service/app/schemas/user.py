from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UserPublic(BaseModel):
    id: int
    email: str
    role: str
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
