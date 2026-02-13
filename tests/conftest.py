import os
import shutil
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Override settings before importing app modules
TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL", "postgresql+asyncpg://alma:alma@localhost:5432/alma_test"
)
os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ["SECRET_KEY"] = "test-secret"
os.environ["UPLOAD_DIR"] = "test_uploads"

from app.database import Base
from app.main import app
from app.api.deps import get_db
from app.models.lead import Lead  # noqa: F401
from app.models.user import User  # noqa: F401
from app.services.auth_service import create_access_token, hash_password


@pytest_asyncio.fixture(autouse=True)
async def db_engine_and_tables():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    yield session_factory

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

    if os.path.exists("test_uploads"):
        shutil.rmtree("test_uploads")


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest_asyncio.fixture
async def seed_user(db_engine_and_tables) -> User:
    session_factory = db_engine_and_tables
    async with session_factory() as session:
        user = User(email="test@alma.com", hashed_password=hash_password("testpass"))
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


@pytest.fixture
def auth_headers(seed_user: User) -> dict[str, str]:
    token = create_access_token({"sub": seed_user.email})
    return {"Authorization": f"Bearer {token}"}
