from fastapi import APIRouter, Depends
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth.security import UserCreate, UserPublic, authenticate, create_access_token, create_user
from app.db.database import get_session

router = APIRouter(prefix="/auth", tags=["Auth"])

class LoginIn(BaseModel):
    email: EmailStr
    password: str

@router.post("/register", response_model=UserPublic)
async def register(payload: UserCreate, session: AsyncSession = Depends(get_session)):
    return await create_user(session, payload.email, payload.password, payload.full_name)

@router.post("/login")
async def login(payload: LoginIn, session: AsyncSession = Depends(get_session)):
    user = await authenticate(session, payload.email, payload.password)
    tok = create_access_token(user.id)
    return {"user": user, "token": tok}
