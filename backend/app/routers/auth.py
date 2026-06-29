from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.auth import verify_password, create_access_token, get_current_user, log_audit, hash_password
from app.models import User, UserRole
from app.schemas import LoginRequest, TokenResponse, UserResponse, UserCreate

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, req: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == request.username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")

    user.last_login = datetime.now(timezone.utc)
    token = create_access_token({"sub": str(user.id), "role": user.role.value})
    await log_audit(db, str(user.id), "login", ip=req.client.host if req.client else None)

    return TokenResponse(
        access_token=token,
        user=UserResponse(
            id=user.id, username=user.username, email=user.email,
            full_name=user.full_name, role=user.role.value,
            badge_number=user.badge_number, station_id=user.station_id,
        ),
    )


@router.get("/me", response_model=UserResponse)
async def get_me(user: User = Depends(get_current_user)):
    return UserResponse(
        id=user.id, username=user.username, email=user.email,
        full_name=user.full_name, role=user.role.value,
        badge_number=user.badge_number, station_id=user.station_id,
    )


@router.post("/register", response_model=UserResponse)
async def register(data: UserCreate, db: AsyncSession = Depends(get_db), admin: User = Depends(get_current_user)):
    if admin.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Admin only")

    existing = await db.execute(select(User).where((User.username == data.username) | (User.email == data.email)))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="User already exists")

    user = User(
        username=data.username, email=data.email,
        password_hash=hash_password(data.password),
        full_name=data.full_name,
        role=UserRole(data.role),
        badge_number=data.badge_number,
        station_id=data.station_id,
    )
    db.add(user)
    await db.flush()
    return UserResponse(
        id=user.id, username=user.username, email=user.email,
        full_name=user.full_name, role=user.role.value,
        badge_number=user.badge_number, station_id=user.station_id,
    )
