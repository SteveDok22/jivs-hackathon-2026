"""Refactoring endpoint: legacy screenshot -> modern Angular component.

Accepts a base64-encoded PNG. Returns the extracted spec, generated code,
and the fidelity report from the self-check loop.
"""

from fastapi import APIRouter
from pydantic import BaseModel

from app.refactor.schemas import RefactorResult
from app.refactor.service import RefactorService

router = APIRouter(prefix="/refactor")


class RefactorRequest(BaseModel):
    image_b64: str
    threshold: float = 0.9
    max_iterations: int = 3


@router.post("", response_model=RefactorResult)
def refactor(request: RefactorRequest) -> RefactorResult:
    service = RefactorService()
    return service.refactor(
        request.image_b64,
        threshold=request.threshold,
        max_iterations=request.max_iterations,
    )
