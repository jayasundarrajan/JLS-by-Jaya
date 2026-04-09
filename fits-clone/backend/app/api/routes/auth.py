#
#  app/api/routes/auth.py
#

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from pydantic import BaseModel

from app.deps import get_db
from app.models.user import User
from app.models.password_credentials import PasswordCredentials

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt_sha256"], deprecated="auto")


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    user_id: str
    username: str
    display_name: str | None


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    # Find user by username
    user = db.query(User).filter(User.username == payload.username).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    # Check password
    creds = db.query(PasswordCredentials).filter(
        PasswordCredentials.user_id == user.id
    ).first()
    if not creds or not pwd_context.verify(payload.password, creds.password_hash):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    return LoginResponse(
        user_id=str(user.id),
        username=user.username,
        display_name=user.display_name,
    )