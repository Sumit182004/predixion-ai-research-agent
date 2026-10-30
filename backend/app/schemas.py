
from typing import Literal
from pydantic import BaseModel, Field, HttpUrl


class ResearchRequest(BaseModel):
    question: str = Field(min_length=10, max_length=1000)


class PlanStep(BaseModel):
    step: int
    action: str
    purpose: str


class ResearchPlan(BaseModel):
    question: str
    steps: list[PlanStep]


class ResearchSource(BaseModel):
    title: str
    url: HttpUrl
    snippet: str = ""


class ExecutionEvent(BaseModel):
    tool: str
    status: Literal["success", "failed", "skipped"]
    message: str


class ResearchResponse(BaseModel):
    user_question: str
    plan: list[PlanStep]
    execution_trace: list[ExecutionEvent]
    short_answer: str
    key_findings: list[str]
    sources_used: list[ResearchSource]
    confidence: Literal["low", "medium", "high"]
    assumptions: list[str]
    limitations: list[str]
    suggested_next_steps: list[str]
