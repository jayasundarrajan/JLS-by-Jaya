from pydantic import BaseModel, Field
from uuid import UUID

class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8, max_length=128)
    display_name: str | None = Field(default=None, max_length=100)

class UserOut(BaseModel):
    id: UUID
    username: str
    display_name: str | None

    class Config:
        from_attributes = True
