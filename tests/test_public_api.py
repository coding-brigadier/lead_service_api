import io

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_submit_lead_success(client: AsyncClient):
    file = io.BytesIO(b"%PDF-1.4 fake pdf content")
    resp = await client.post(
        "/leads",
        data={"first_name": "Jane", "last_name": "Doe", "email": "jane@example.com"},
        files={"resume": ("resume.pdf", file, "application/pdf")},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["state"] == "PENDING"
    assert "id" in body


@pytest.mark.asyncio
async def test_submit_lead_invalid_file_type(client: AsyncClient):
    file = io.BytesIO(b"not a resume")
    resp = await client.post(
        "/leads",
        data={"first_name": "Jane", "last_name": "Doe", "email": "jane@example.com"},
        files={"resume": ("resume.txt", file, "text/plain")},
    )
    assert resp.status_code == 400
    assert "not allowed" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_submit_lead_missing_fields(client: AsyncClient):
    resp = await client.post("/leads", data={"first_name": "Jane"})
    assert resp.status_code == 422
