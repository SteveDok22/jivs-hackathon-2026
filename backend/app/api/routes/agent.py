"""Agent endpoint: ask a question over a dataset directory."""

from fastapi import APIRouter
from pydantic import BaseModel

from app.agent.agent import AgentAnswer, DataAgent

router = APIRouter(prefix="/agent")


class AskRequest(BaseModel):
    question: str
    directory: str = "data/synthetic"


@router.post("/ask", response_model=AgentAnswer)
def ask(request: AskRequest) -> AgentAnswer:
    agent = DataAgent(request.directory)
    return agent.ask(request.question)
