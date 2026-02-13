import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, Token
from app.schemas.lead import LeadPage, LeadRead, LeadUpdateState
from app.services.auth_service import authenticate_user, create_access_token
from app.services.lead_service import get_lead, list_leads, update_lead_state

router = APIRouter()


@router.post("/auth/login", response_model=Token)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate an internal user and return a JWT access token."""
    user = await authenticate_user(db, body.email, body.password)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials.")
    token = create_access_token({"sub": user.email})
    return Token(access_token=token)


@router.get("/leads", response_model=LeadPage)
async def get_leads(
    limit: int = Query(20, ge=1, le=100),
    cursor: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    """List all leads with cursor-based pagination (newest first)."""
    return await list_leads(db, limit=limit, cursor=cursor)


@router.get("/leads/{lead_id}", response_model=LeadRead)
async def get_lead_detail(
    lead_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    """Retrieve a single lead by ID."""
    return await get_lead(db, lead_id)


@router.patch("/leads/{lead_id}", response_model=LeadRead)
async def patch_lead(
    lead_id: uuid.UUID,
    body: LeadUpdateState,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    """Update a lead's state (e.g. PENDING -> REACHED_OUT)."""
    return await update_lead_state(db, lead_id, body.state)
