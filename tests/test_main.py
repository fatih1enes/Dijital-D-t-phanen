import pytest

pytestmark = pytest.mark.asyncio


async def test_read_main(async_client):
    response = await async_client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


async def test_auth_status(async_client):
    response = await async_client.get("/api/auth/status")
    assert response.status_code == 200
    data = response.json()
    assert "authenticated" in data
    assert "required" in data
    assert "locked" in data


async def test_get_books_pagination(async_client):
    response = await async_client.get("/api/books?page=1&limit=10")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "items" in data
    assert "limit" in data
    assert "offset" in data
    assert data["limit"] == 10
    assert data["offset"] == 0
    assert isinstance(data["items"], list)


async def test_get_tasks(async_client):
    response = await async_client.get("/api/tasks")
    assert response.status_code == 200
    data = response.json()
    assert "active" in data
    assert "archived" in data
