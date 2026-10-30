
from app.schemas import ResearchResponse


def evaluate_response(response: ResearchResponse) -> dict:
    checks = {
        "has_short_answer": bool(response.short_answer.strip()),

        "has_plan": len(response.plan) >= 1,

        "has_execution_trace": len(response.execution_trace) >= 1,

        "has_findings_or_low_confidence": (
            len(response.key_findings) >= 1
            or response.confidence == "low"
        ),

        "has_source_metadata": all(
            bool(source.title.strip()) and bool(str(source.url))
            for source in response.sources_used
        ),

        "has_limitations_when_confidence_is_low": (
            response.confidence != "low"
            or len(response.limitations) > 0
        ),

        "high_confidence_has_multiple_sources": (
            response.confidence != "high"
            or len(response.sources_used) >= 2
        ),

        "failed_events_have_explanations": all(
            bool(event.message.strip())
            for event in response.execution_trace
            if event.status == "failed"
        ),
    }

    passed = sum(checks.values())
    total = len(checks)

    return {
        "passed": passed,
        "total": total,
        "score": round(passed / total, 2),
        "checks": checks,
    }