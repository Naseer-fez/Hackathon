"""Telemetry middleware for FastAPI."""
import time
from typing import Any
from fastapi import Request, Response
from backend.logger.app_logger import get_logger
from backend.metrics import REQUEST_COUNT, REQUEST_LATENCY

logger = get_logger("middleware.telemetry")

async def log_requests_middleware(request: Request, call_next: Any) -> Response:
    """Log all incoming HTTP requests and response performance metrics."""
    start_time = time.perf_counter()
    client_ip = request.client.host if request.client else "127.0.0.1"
    logger.info(f"--> {request.method} {request.url.path} [Client: {client_ip}]")
    try:
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        REQUEST_COUNT.labels(
            method=request.method, endpoint=request.url.path, status_code=str(response.status_code)
        ).inc()
        REQUEST_LATENCY.labels(method=request.method, endpoint=request.url.path).observe(elapsed_ms / 1000.0)
        logger.info(f"<-- {request.method} {request.url.path} [{response.status_code}] ({elapsed_ms:.2f}ms)")
        return response
    except Exception as exc:
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        REQUEST_COUNT.labels(method=request.method, endpoint=request.url.path, status_code="500").inc()
        REQUEST_LATENCY.labels(method=request.method, endpoint=request.url.path).observe(elapsed_ms / 1000.0)
        logger.error(
            f"<-- {request.method} {request.url.path} [EXCEPTION: {type(exc).__name__} - {exc}] ({elapsed_ms:.2f}ms)"
        )
        raise
