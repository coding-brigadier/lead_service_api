import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lead import Lead, LeadState
from app.pagination import paginate
from app.schemas.lead import LeadPage


async def create_lead(
    db: AsyncSession,
    first_name: str,
    last_name: str,
    email: str,
    resume_path: str,
) -> Lead:
    """Create a new lead in PENDING state and persist it to the database."""
    lead = Lead(
        first_name=first_name,
        last_name=last_name,
        email=email,
        resume_path=resume_path,
    )
    db.add(lead)
    await db.commit()
    await db.refresh(lead)
    return lead


async def list_leads(
    db: AsyncSession,
    limit: int = 20,
    cursor: str | None = None,
) -> LeadPage:
    """Return a cursor-paginated list of leads, newest first."""
    query = select(Lead)
    rows, next_cursor = await paginate(
        db, query, Lead.created_at, Lead.id, cursor, limit
    )
    return LeadPage(items=rows, next_cursor=next_cursor)


async def get_lead(db: AsyncSession, lead_id: uuid.UUID) -> Lead:
    """Fetch a single lead by ID, or raise 404 if not found."""
    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = result.scalar_one_or_none()
    if lead is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found.")
    return lead


async def update_lead_state(db: AsyncSession, lead_id: uuid.UUID, new_state: LeadState) -> Lead:
    """Transition a lead to a new state. Raises 400 for invalid transitions."""
    lead = await get_lead(db, lead_id)
    if lead.state == new_state:
        return lead
    if lead.state == LeadState.REACHED_OUT and new_state == LeadState.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot transition from REACHED_OUT back to PENDING.",
        )
    lead.state = new_state
    await db.commit()
    await db.refresh(lead)
    return lead
