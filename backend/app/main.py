"""FastAPI application entry point.

Stage 0 exposes only /health. Every later stage plugs its router in here:
    Stage 3 -> app.include_router(pii.router)
    Stage 4 -> app.include_router(agent.router)
    Stage 5 -> guardrails middleware
"""

from fastapi import FastAPI

from app.api.routes import health
from app.config import get_settings

settings = get_settings()

app = FastAPI(
    title="Trusted Enterprise Agent",
    version=settings.version,
    description="JiVS Hackathon 2026 — secured AI agent over cleansed enterprise data.",
)

app.include_router(health.router, tags=["system"])
