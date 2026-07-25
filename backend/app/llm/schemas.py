"""Shared LLM data structures."""

from pydantic import BaseModel


class Usage(BaseModel):
    input_tokens: int = 0
    output_tokens: int = 0


class LLMResult(BaseModel):
    text: str
    model: str
    usage: Usage
