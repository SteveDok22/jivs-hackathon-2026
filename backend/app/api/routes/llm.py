"""LLM usage endpoint — raw feed for the Stage 6 eval panel."""

from fastapi import APIRouter

from app.llm.cost import get_meter

router = APIRouter(prefix="/llm")


@router.get("/usage")
def usage() -> dict:
    return get_meter().snapshot()
