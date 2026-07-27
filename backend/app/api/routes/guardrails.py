"""Guardrails endpoints: test the input filter and output scanner directly.

Useful for the demo and for the red-team panel (Stage 6).
"""

from fastapi import APIRouter
from pydantic import BaseModel

from app.guardrails.input_filter import inspect_input
from app.guardrails.output_filter import inspect_output

router = APIRouter(prefix="/guardrails")


class InputRequest(BaseModel):
    text: str


@router.post("/input")
def check_input(request: InputRequest) -> dict:
    result = inspect_input(request.text)
    return vars(result)


@router.post("/output")
def check_output(request: InputRequest) -> dict:
    result = inspect_output(request.text)
    return vars(result)
