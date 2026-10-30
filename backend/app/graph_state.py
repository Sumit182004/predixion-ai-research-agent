
from typing import Any, TypedDict

from app.schemas import ResearchResponse


class ResearchState(TypedDict, total=False):
    question: str

    plan: Any
    search_result: dict[str, Any]
    candidates: list[dict[str, Any]]

    evidence: list[dict[str, Any]]
    sources: list[Any]
    quality_result: dict[str, Any]

    trace: list[Any]
    limitations: list[str]

    response: ResearchResponse
