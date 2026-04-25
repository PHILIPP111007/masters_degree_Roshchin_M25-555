from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    prompt: str = Field(..., min_length=1, description="User message text")
    system: str | None = Field(None, description="Optional system instruction")
    max_history: int = Field(
        10, ge=0, le=50, description="Number of previous messages to include"
    )
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="Model temperature")


class ChatResponse(BaseModel):
    answer: str


class ChatMessagePublic(BaseModel):
    id: int
    role: str
    content: str
    created_at: str | None = None

    model_config = {"from_attributes": True}
