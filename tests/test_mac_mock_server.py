"""Unit tests for mock Mac reasoning server."""
from __future__ import annotations
from typing import AsyncGenerator
from fastapi.testclient import TestClient
import pytest
from backend.engine.llm_interface import BaseLlmProvider
import backend.mac_mock_server as mock_module
from backend.mac_mock_server import app


class MockCloudProviderForMac(BaseLlmProvider):
    async def generate_text(self, prompt: str, system_prompt: str | None = None) -> str:
        return "Deep Mac Reasoning: IS 1786 Fe 500D conforms to CRS mandatory scheme."

    async def generate_text_stream(self, prompt: str, system_prompt: str | None = None) -> AsyncGenerator[str, None]:
        yield "Deep Mac Reasoning: IS 1786"


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_mac_mock_health(client: TestClient) -> None:
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "online"
    assert "device" in data


def test_mac_mock_reason(client: TestClient) -> None:
    # Inject mock cloud reasoner to isolate test
    original = mock_module.cloud_reasoner
    mock_module.cloud_reasoner = MockCloudProviderForMac()
    try:
        payload = {
            "prompt": "Evaluate IS 1786 compliance",
            "system_prompt": "You are a Mac reasoning engine",
            "stream": False,
        }
        res = client.post("/reason", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert "Deep Mac Reasoning" in data["response"]
        assert data["source"] == "mac_m3_cloud_bridge"
    finally:
        mock_module.cloud_reasoner = original


def test_mac_mock_reason_stream(client: TestClient) -> None:
    original = mock_module.cloud_reasoner
    mock_module.cloud_reasoner = MockCloudProviderForMac()
    try:
        payload = {
            "prompt": "Evaluate IS 1786 compliance",
            "stream": True,
        }
        res = client.post("/reason", json=payload)
        assert res.status_code == 200
        assert "Deep Mac Reasoning" in res.text
    finally:
        mock_module.cloud_reasoner = original


@pytest.mark.asyncio
async def test_remote_mac_llm_provider_integration() -> None:
    import httpx
    original = mock_module.cloud_reasoner
    mock_module.cloud_reasoner = MockCloudProviderForMac()
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            res = await client.post("http://test/reason", json={"prompt": "IS 1786 test"})
            assert res.status_code == 200
            data = res.json()
            assert "Deep Mac Reasoning" in data["response"]
    finally:
        mock_module.cloud_reasoner = original

