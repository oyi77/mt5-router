from fastapi import APIRouter, HTTPException, status
from passlib.context import CryptContext
import hashlib
import os

from app.auth.jwt import create_access_token
from app.auth.models import UserLogin, TokenResponse

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

DEFAULT_USERS = {
    "admin": {
        "id": "1",
        "username": "admin",
        "password_hash": pwd_context.hash("admin123"),
        "role": "admin",
    }
}


@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    user = DEFAULT_USERS.get(credentials.username)
    if not user or not pwd_context.verify(credentials.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )

    token = create_access_token(
        {"sub": user["id"], "username": user["username"], "role": user["role"]}
    )
    return TokenResponse(access_token=token)


@router.get("/me")
async def get_me(token: dict):
    return {
        "id": token.get("sub"),
        "username": token.get("username"),
        "role": token.get("role"),
    }
