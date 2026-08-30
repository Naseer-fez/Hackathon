"""Unit tests for structured logging and HTTP request middleware."""
from __future__ import annotations

import logging
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from backend.config.settings import app_settings
from backend.logger.app_logger import ColoredFormatter, get_logger, setup_logging
from backend.main import app


@pytest.fixture
def client() -> TestClient:
    """Fixture providing FastAPI test client."""
    return TestClient(app)


def test_setup_logging_creates_directory_and_file() -> None:
    """Verify setup_logging creates the logs directory and backend.log file."""
    setup_logging()
    log_dir = Path(app_settings.logging.log_dir)
    assert log_dir.exists()
    assert log_dir.is_dir()

    logger = get_logger("test_module")
    logger.info("Test log entry for directory verification")

    log_file = Path(app_settings.logging.log_file)
    assert log_file.exists()
    content = log_file.read_text(encoding="utf-8")
    assert "Test log entry for directory verification" in content


def test_colored_formatter() -> None:
    """Verify ColoredFormatter applies ANSI color codes to log record levels."""
    formatter = ColoredFormatter("%(levelname)s - %(message)s")
    record = logging.LogRecord(
        name="test",
        level=logging.WARNING,
        pathname="test.py",
        lineno=10,
        msg="[FALLBACK] Model unavailable",
        args=(),
        exc_info=None,
    )
    formatted = formatter.format(record)
    assert "\033[33m" in formatted  # Yellow for WARNING
    assert "[FALLBACK]" in formatted


def test_http_request_logging_middleware(client: TestClient) -> None:
    """Verify HTTP middleware logs request and response status."""
    res = client.get("/api/v1/health")
    assert res.status_code == 200

    log_file = Path(app_settings.logging.log_file)
    assert log_file.exists()
    content = log_file.read_text(encoding="utf-8")
    assert "--> GET /api/v1/health" in content
    assert "<-- GET /api/v1/health [200]" in content
