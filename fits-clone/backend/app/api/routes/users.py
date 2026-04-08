from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from app.deps import get_db
from app.models.user import User
from app.models.auth_identity import AuthIdentity
from app.models.password_credentials import PasswordCredentials
from app.schemas.user import UserCreate, UserOut

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt_sha256"], deprecated="auto")

@router.post("", response_model=UserOut)
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    # username uniqueness
    existing = db.query(User).filter(User.username == payload.username).first()
    if existing:
        raise HTTPException(status_code=409, detail="Username already taken")

    user = User(username=payload.username, display_name=payload.display_name)
    db.add(user)
    db.flush()  # get user.id without committing yet

    # Auth identity for password login
    auth = AuthIdentity(
        user_id=user.id,
        provider="password",
        provider_user_id=payload.username
    )
    db.add(auth)

    # Password credentials
    pw = PasswordCredentials(
        user_id=user.id,
        password_hash=pwd_context.hash(payload.password),
    )
    db.add(pw)

    db.commit()
    db.refresh(user)
    return user
