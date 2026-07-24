"""Health endpoint.

The deploy target for hour one of the hackathon: if /health answers
in the cloud, the pipeline (code -> CI -> deploy) is proven and the
team can focus on the actual task.
"""

from fastapi import APIRouter
from pydantic import BaseModel

from app.config import get_settings

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    environment: str


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        status="ok",
        service=settings.app_name,
        version=settings.version,
        environment=settings.app_env,
    )
