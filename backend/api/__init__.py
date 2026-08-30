"""API routers package."""
from backend.api.gem_webhook_router import router as gem_router
from backend.api.llm_router import router as llm_router
from backend.api.pipeline_router import router as pipeline_router
from backend.api.recommendation_router import router as rec_router
from backend.api.standards_router import router as std_router
from backend.api.tender_router import router as tender_router

__all__ = [
    "gem_router",
    "llm_router",
    "pipeline_router",
    "rec_router",
    "std_router",
    "tender_router",
]
