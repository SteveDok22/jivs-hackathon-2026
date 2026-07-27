"""FastAPI application entry point.

Each stage plugs its router in here:
    Stage 0 -> health
    Stage 1 -> llm (usage meter + ping)
    Stage 3 -> pii
    Stage 4 -> agent
    Stage 5 -> guardrails middleware
"""

from fastapi import FastAPI

from app.api.routes import agent, guardrails, health, llm, pii
from app.config import get_settings

settings = get_settings()

app = FastAPI(
    title="Trusted Enterprise Agent",
    version=settings.version,
    description="JiVS Hackathon 2026 — secured AI agent over cleansed enterprise data.",
)

app.include_router(health.router, tags=["system"])
app.include_router(llm.router, tags=["llm"])
app.include_router(pii.router, tags=["pii"])
app.include_router(agent.router, tags=["agent"])
app.include_router(guardrails.router, tags=["guardrails"])
app.include_router(llm.router, tags=["llm"])
app.include_router(pii.router, tags=["pii"])
app.include_router(agent.router, tags=["agent"])
app.include_router(guardrails.router, tags=["guardrails"])
