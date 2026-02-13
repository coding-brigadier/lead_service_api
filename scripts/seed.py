"""Seed an initial internal user.

Usage:
    python -m scripts.seed
"""

import asyncio
import sys
from pathlib import Path

# Ensure project root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select

from app.database import Base, async_session_factory, engine
from app.models.user import User
from app.services.auth_service import hash_password

DEFAULT_EMAIL = "admin@alma.com"
DEFAULT_PASSWORD = "changeme123"


async def seed():
    """Create the default internal user if it doesn't already exist."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_factory() as session:
        result = await session.execute(select(User).where(User.email == DEFAULT_EMAIL))
        if result.scalar_one_or_none() is not None:
            print(f"User {DEFAULT_EMAIL} already exists — skipping.")
            return

        user = User(email=DEFAULT_EMAIL, hashed_password=hash_password(DEFAULT_PASSWORD))
        session.add(user)
        await session.commit()
        print(f"Created user {DEFAULT_EMAIL} with password '{DEFAULT_PASSWORD}'")


if __name__ == "__main__":
    asyncio.run(seed())
