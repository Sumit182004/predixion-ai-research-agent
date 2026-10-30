
from app.schemas import PlanStep, ResearchPlan


def create_plan(question: str) -> ResearchPlan:
    """Create an explicit plan for the research workflow."""

    steps = [
        PlanStep(
            step=1,
            action="web_search",
            purpose="Find relevant sources for the research question.",
        ),
        PlanStep(
            step=2,
            action="filter_sources",
            purpose="Remove duplicate, incomplete, or irrelevant results.",
        ),
        PlanStep(
            step=3,
            action="fetch_pages",
            purpose="Retrieve page content to verify important findings.",
        ),
        PlanStep(
            step=4,
            action="synthesize",
            purpose="Produce a structured answer grounded in retrieved evidence.",
        ),
    ]

    return ResearchPlan(question=question, steps=steps)
