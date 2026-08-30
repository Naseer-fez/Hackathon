"""Integration tests for FastAPI REST endpoints."""
from __future__ import annotations

from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_health_endpoint() -> None:
    """Test health check route."""
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"


def test_recommend_endpoint_english() -> None:
    """Test standard recommendation route with English query."""
    payload = {"query": "Supply of TMT steel rebar Fe 500D", "top_k": 3}
    res = client.post("/api/v1/recommend", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["total_matches"] > 0
    assert "1786" in data["recommendations"][0]["standard"]["is_code"]


def test_recommend_endpoint_hindi() -> None:
    """Test standard recommendation with Hindi Indic query."""
    payload = {"query": "सौर पैनल और ग्रिड इनवर्टर", "top_k": 2}
    res = client.post("/api/v1/recommend", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["detected_language"] == "hi"
    assert len(data["recommendations"]) > 0


def test_standards_and_graph_endpoints() -> None:
    """Test standards listing, single standard, and graph retrieval."""
    res = client.get("/api/v1/standards")
    assert res.status_code == 200
    assert len(res.json()) > 0

    res_single = client.get("/api/v1/standards/IS 456")
    assert res_single.status_code == 200
    assert res_single.json()["is_code"] == "IS 456"

    res_graph = client.get("/api/v1/graph")
    assert res_graph.status_code == 200
    assert "nodes" in res_graph.json()
    assert "edges" in res_graph.json()


def test_gem_webhook_endpoint() -> None:
    """Test GeM portal webhook simulation endpoint."""
    payload = {
        "bid_id": "GEM-2026-B-99881",
        "category_name": "Power Distribution",
        "product_title": "Distribution Transformer 2500 kVA",
        "buyer_specifications": "Outdoor type 33kV energy efficient copper wound",
    }
    res = client.post("/api/v1/gem-webhook", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["bid_id"] == "GEM-2026-B-99881"
    assert "1180" in data["primary_standard"]
    assert data["is_qco_mandatory"] is True


def test_analyze_tender_endpoint() -> None:
    """Test tender document text analysis."""
    payload = {
        "raw_text": "Item 1: 500 units of LED street lights 120W.\n\nItem 2: 50 units of fire extinguishers ABC type."
    }
    res = client.post("/api/v1/analyze-tender", data=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["extracted_items_count"] == 2
    assert len(data["items"]) == 2
