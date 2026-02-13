import pytest
from httpx import AsyncClient

from app.models.user import User


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, seed_user: User):
    resp = await client.post("/auth/login", json={"email": "test@alma.com", "password": "testpass"})
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient, seed_user: User):
    resp = await client.post("/auth/login", json={"email": "test@alma.com", "password": "wrong"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_nonexistent_user(client: AsyncClient):
    resp = await client.post("/auth/login", json={"email": "nobody@example.com", "password": "test"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_protected_route_with_login_token(client: AsyncClient, seed_user: User):
    login_resp = await client.post("/auth/login", json={"email": "test@alma.com", "password": "testpass"})
    token = login_resp.json()["access_token"]

    resp = await client.get("/leads", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
