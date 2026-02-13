from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    """Request body for the login endpoint."""

    email: EmailStr
    password: str


class Token(BaseModel):
    """JWT token response returned after successful authentication."""

    access_token: str
    token_type: str = "bearer"
