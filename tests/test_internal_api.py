import io

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_leads_unauthenticated(client: AsyncClient):
    resp = await client.get("/leads")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_list_leads(client: AsyncClient, auth_headers: dict):
    # Create a lead first
    file = io.BytesIO(b"%PDF-1.4 content")
    await client.post(
        "/leads",
        data={"first_name": "John", "last_name": "Smith", "email": "john@example.com"},
        files={"resume": ("cv.pdf", file, "application/pdf")},
    )

    resp = await client.get("/leads", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["items"]) >= 1
    assert body["items"][0]["first_name"] == "John"


@pytest.mark.asyncio
async def test_get_lead_detail(client: AsyncClient, auth_headers: dict):
    file = io.BytesIO(b"%PDF-1.4 content")
    create_resp = await client.post(
        "/leads",
        data={"first_name": "Alice", "last_name": "Wonder", "email": "alice@example.com"},
        files={"resume": ("cv.pdf", file, "application/pdf")},
    )
    lead_id = create_resp.json()["id"]

    resp = await client.get(f"/leads/{lead_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["email"] == "alice@example.com"


@pytest.mark.asyncio
async def test_update_lead_state(client: AsyncClient, auth_headers: dict):
    file = io.BytesIO(b"%PDF-1.4 content")
    create_resp = await client.post(
        "/leads",
        data={"first_name": "Bob", "last_name": "Builder", "email": "bob@example.com"},
        files={"resume": ("cv.pdf", file, "application/pdf")},
    )
    lead_id = create_resp.json()["id"]

    resp = await client.patch(f"/leads/{lead_id}", json={"state": "REACHED_OUT"}, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["state"] == "REACHED_OUT"


@pytest.mark.asyncio
async def test_update_lead_state_invalid_transition(client: AsyncClient, auth_headers: dict):
    file = io.BytesIO(b"%PDF-1.4 content")
    create_resp = await client.post(
        "/leads",
        data={"first_name": "Charlie", "last_name": "Brown", "email": "charlie@example.com"},
        files={"resume": ("cv.pdf", file, "application/pdf")},
    )
    lead_id = create_resp.json()["id"]

    # First transition to REACHED_OUT
    await client.patch(f"/leads/{lead_id}", json={"state": "REACHED_OUT"}, headers=auth_headers)

    # Attempt invalid transition back to PENDING
    resp = await client.patch(f"/leads/{lead_id}", json={"state": "PENDING"}, headers=auth_headers)
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_cursor_pagination(client: AsyncClient, auth_headers: dict):
    # Create 3 leads
    for name in ["A", "B", "C"]:
        file = io.BytesIO(b"%PDF-1.4 content")
        await client.post(
            "/leads",
            data={"first_name": name, "last_name": "Test", "email": f"{name.lower()}@example.com"},
            files={"resume": ("cv.pdf", file, "application/pdf")},
        )

    # Page 1: limit=2
    resp = await client.get("/leads", params={"limit": 2}, headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["items"]) == 2
    assert body["next_cursor"] is not None

    # Page 2: use cursor
    resp2 = await client.get("/leads", params={"limit": 2, "cursor": body["next_cursor"]}, headers=auth_headers)
    assert resp2.status_code == 200
    body2 = resp2.json()
    assert len(body2["items"]) == 1
    assert body2["next_cursor"] is None

    # No overlap between pages
    page1_ids = {item["id"] for item in body["items"]}
    page2_ids = {item["id"] for item in body2["items"]}
    assert page1_ids.isdisjoint(page2_ids)


@pytest.mark.asyncio
async def test_get_nonexistent_lead(client: AsyncClient, auth_headers: dict):
    resp = await client.get("/leads/00000000-0000-0000-0000-000000000000", headers=auth_headers)
    assert resp.status_code == 404
