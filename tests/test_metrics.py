"""Tests for Prometheus metrics endpoint."""
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.metrics import REQUEST_COUNT, GPU_VRAM_USAGE

from prometheus_client.parser import text_string_to_metric_families

client = TestClient(app)

def test_metrics_endpoint() -> None:
    """Test the /metrics endpoint returns valid prometheus text format."""
    # First make a health check request to increment the counter
    client.get("/api/v1/health")
    
    # Now get metrics
    response = client.get("/metrics")
    
    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]
    
    # Check that metrics are present by parsing them
    text = response.text
    metrics = list(text_string_to_metric_families(text))
    
    metric_names = [m.name for m in metrics]
    
    assert "bisspecai_http_requests" in metric_names or "bisspecai_http_requests_total" in metric_names
    assert "bisspecai_gpu_vram_bytes" in metric_names
