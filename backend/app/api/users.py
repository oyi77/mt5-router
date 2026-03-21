from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from passlib.context import CryptContext
import secrets
from datetime import datetime, timedelta

from app.core.database import get_db
from app.models.database import User, ApiKey, UserRole
from app.auth.jwt import get_current_user, create_access_token

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@router.post("/register")
async def register(
    email: str,
    username: str,
    password: str,
    full_name: str = None,
    db: Session = Depends(get_db),
):
    if (
        db.query(User)
        .filter((User.email == email) | (User.username == username))
        .first()
    ):
        raise HTTPException(status_code=400, detail="User already exists")

    user = User(
        email=email,
        username=username,
        hashed_password=pwd_context.hash(password),
        full_name=full_name,
        role=UserRole.USER,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(
        {"sub": str(user.id), "username": user.username, "role": user.role}
    )
    return {"access_token": token, "token_type": "bearer", "user_id": user.id}


@router.get("/me")
async def get_me(user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == int(user["sub"])).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "id": db_user.id,
        "email": db_user.email,
        "username": db_user.username,
        "full_name": db_user.full_name,
        "role": db_user.role,
        "created_at": db_user.created_at,
    }


@router.put("/me")
async def update_me(
    full_name: str = None,
    email: str = None,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    db_user = db.query(User).filter(User.id == int(user["sub"])).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    if full_name:
        db_user.full_name = full_name
    if email:
        db_user.email = email
    db.commit()
    return {"status": "updated"}


@router.post("/api-keys")
async def create_api_key(
    name: str,
    permissions: list = None,
    expires_days: int = 365,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    api_key = ApiKey(
        key=f"mtr_{secrets.token_hex(32)}",
        name=name,
        user_id=int(user["sub"]),
        permissions=",".join(permissions) if permissions else "read,trade",
        expires_at=datetime.utcnow() + timedelta(days=expires_days),
    )
    db.add(api_key)
    db.commit()
    db.refresh(api_key)

    return {
        "id": api_key.id,
        "key": api_key.key,
        "name": api_key.name,
        "expires_at": api_key.expires_at,
    }


@router.get("/api-keys")
async def list_api_keys(
    user: dict = Depends(get_current_user), db: Session = Depends(get_db)
):
    keys = db.query(ApiKey).filter(ApiKey.user_id == int(user["sub"])).all()
    return [
        {
            "id": k.id,
            "name": k.name,
            "is_active": k.is_active,
            "last_used": k.last_used,
            "created_at": k.created_at,
        }
        for k in keys
    ]


@router.delete("/api-keys/{key_id}")
async def delete_api_key(
    key_id: int, user: dict = Depends(get_current_user), db: Session = Depends(get_db)
):
    key = (
        db.query(ApiKey)
        .filter(ApiKey.id == key_id, ApiKey.user_id == int(user["sub"]))
        .first()
    )
    if not key:
        raise HTTPException(status_code=404, detail="API key not found")
    db.delete(key)
    db.commit()
    return {"status": "deleted"}
