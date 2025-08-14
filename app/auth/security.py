from __future__ import annotations
from datetime import datetime, timedelta, timezone
from typing import Annotated, Optional
import os
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt, JWTError
from passlib.hash import bcrypt
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_session
from app.db.models import User

JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret")

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None

class UserPublic(BaseModel):
    id: str
    email: EmailStr
    full_name: Optional[str] = None

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int

def hash_password(pw: str) -> str:
    return bcrypt.hash(pw)

def verify_password(pw: str, hashed: str) -> bool:
    return bcrypt.verify(pw, hashed)

def _now_utc():
    return datetime.now(timezone.utc)

def create_access_token(sub: str, expires_minutes: int = 60) -> TokenOut:
    expire = _now_utc() + timedelta(minutes=expires_minutes)
    to_encode = {"sub": sub, "exp": int(expire.timestamp())}
    token = jwt.encode(to_encode, JWT_SECRET, algorithm="HS256")
    return TokenOut(access_token=token, expires_in=expires_minutes * 60)

bearer_scheme = HTTPBearer()

async def get_current_user(
    creds: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> UserPublic:
    token = creds.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        sub = payload.get("sub")
        if not sub:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token.")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token.")
    user = await session.scalar(select(User).where(User.id == sub))
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token.")
    return UserPublic(id=user.id, email=user.email, full_name=user.full_name)

async def create_user(session: AsyncSession, email: str, password: str, full_name: Optional[str]) -> UserPublic:
    exists = await session.scalar(select(User).where(User.email == email.lower()))
    if exists:
        raise HTTPException(409, "User already exists.")
    u = User(email=email.lower(), full_name=full_name, password_hash=hash_password(password))
    session.add(u)
    await session.commit()
    await session.refresh(u)
    return UserPublic(id=u.id, email=u.email, full_name=u.full_name)

async def authenticate(session: AsyncSession, email: str, password: str) -> UserPublic:
    u = await session.scalar(select(User).where(User.email == email.lower()))
    if not u or not verify_password(password, u.password_hash):
        raise HTTPException(401, "Invalid credentials.")
    return UserPublic(id=u.id, email=u.email, full_name=u.full_name)
