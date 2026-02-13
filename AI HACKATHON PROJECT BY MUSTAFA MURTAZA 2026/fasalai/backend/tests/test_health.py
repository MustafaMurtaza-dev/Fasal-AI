"""
FasalAI — Smoke tests for health endpoint
Run: python -m pytest tests/test_health.py -v
"""
import pytest
from httpx import ASGITransport, AsyncClient

from main import app


@pytest.fixture
def client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


@pytest.mark.asyncio
async def test_root_returns_200(client):
    """Root endpoint should return 200 and include service info."""
    async with client as c:
        r = await c.get("/")
    assert r.status_code == 200
    data = r.json()
    assert "name" in data
    assert data["status"] == "operational ✅"


@pytest.mark.asyncio
async def test_health_returns_200(client):
    """Health endpoint should return 200 with model information."""
    async with client as c:
        r = await c.get("/api/v1/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "healthy"
    assert "models" in data
    assert "primary" in data["models"]
    assert "fast" in data["models"]
    assert "backup" in data["models"]
    # EXTRA_MODEL was removed — should NOT be present
    assert "extra" not in data["models"]


@pytest.mark.asyncio
async def test_health_model_values_not_empty(client):
    """All model values should be non-empty strings."""
    async with client as c:
        r = await c.get("/api/v1/health")
    models = r.json()["models"]
    for key in ["primary", "fast", "backup"]:
        assert isinstance(models[key], str)
        assert len(models[key]) > 0
