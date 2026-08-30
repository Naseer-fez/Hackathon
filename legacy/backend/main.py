"""FastAPI application entry point for Indian Standards AI Recommendation Engine."""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from backend.api.gem_webhook_router import router as gem_router
from backend.api.llm_router import router as llm_router
from backend.api.recommendation_router import router as rec_router
from backend.api.standards_router import router as std_router
from backend.api.tender_router import router as tender_router
from backend.config.settings import app_settings
from backend.data.seed_generator import generate_seed_data


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan context ensuring seed data and embeddings are loaded."""
    generate_seed_data()
    yield


app = FastAPI(
    title="BIS Indian Standards AI Recommendation Engine",
    description="AI-powered recommendation engine for Indian Standards (IS), QCO compliance, and tender specification auditing.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=app_settings.server.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(rec_router)
app.include_router(tender_router)
app.include_router(std_router)
app.include_router(gem_router)
app.include_router(llm_router)


@app.get("/api/v1/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy", "service": "Indian Standards AI Engine", "version": "1.0.0"}


def start_server() -> None:
    """Run uvicorn server with configured parameters."""
    uvicorn.run(
        "backend.main:app",
        host=app_settings.server.host,
        port=app_settings.server.port,
        log_level=app_settings.server.log_level.lower(),
        reload=False,
    )


if __name__ == "__main__":
    start_server()
