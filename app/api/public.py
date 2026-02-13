import asyncio
import logging

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.schemas.lead import LeadCreateResponse
from app.services.email_service import send_attorney_notification, send_prospect_confirmation
from app.services.lead_service import create_lead
from app.utils.file_upload import save_resume

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/leads", status_code=status.HTTP_201_CREATED, response_model=LeadCreateResponse)
async def submit_lead(
    first_name: str = Form(...),
    last_name: str = Form(...),
    email: str = Form(...),
    resume: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """Submit a new lead with contact info and a resume file (PDF/DOC/DOCX)."""
    resume_path = await save_resume(resume)

    lead = await create_lead(db, first_name=first_name, last_name=last_name, email=email, resume_path=resume_path)

    # Fire-and-forget emails — don't block the response
    async def _send_emails():
        try:
            await asyncio.gather(
                send_prospect_confirmation(email, first_name),
                send_attorney_notification(email, first_name, last_name),
            )
        except Exception:
            logger.exception("Failed to send lead notification emails")

    asyncio.create_task(_send_emails())

    return lead
