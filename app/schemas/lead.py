import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr

from app.models.lead import LeadState
from app.pagination import Page


class LeadCreateResponse(BaseModel):
    id: uuid.UUID
    state: LeadState

    model_config = {"from_attributes": True}


class LeadRead(BaseModel):
    id: uuid.UUID
    first_name: str
    last_name: str
    email: EmailStr
    resume_path: str
    state: LeadState
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


LeadPage = Page[LeadRead]


class LeadUpdateState(BaseModel):
    state: LeadState
