
from app.evaluator import evaluate_response
from app.schemas import (
    ExecutionEvent,
    PlanStep,
    ResearchResponse,
    ResearchSource,
)


def make_response(
    confidence="medium",
    sources=None,
    limitations=None,
    short_answer="A test research answer.",
):
    return ResearchResponse(
        user_question="Compare vector databases for RAG applications",
        plan=[
            PlanStep(
                step=1,
                action="web_search",
                purpose="Find relevant evidence.",
            )
        ],
        execution_trace=[
            ExecutionEvent(
                tool="web_search",
                status="success",
                message="Retrieved test results.",
            )
        ],
        short_answer=short_answer,
        key_findings=["Finding supported by retrieved evidence."],
        sources_used=sources or [],
        confidence=confidence,
        assumptions=[],
        limitations=limitations or [],
        suggested_next_steps=["Verify results with a workload benchmark."],
    )


def test_case_1_complete_answer():
    response = make_response(
        sources=[
            ResearchSource(
                title="Source A",
                url="https://example.com/a",
                snippet="Relevant evidence.",
            ),
            ResearchSource(
                title="Source B",
                url="https://example.com/b",
                snippet="Additional evidence.",
            ),
        ],
        confidence="high",
    )

    result = evaluate_response(response)
    assert result["checks"]["has_short_answer"]
    assert result["checks"]["has_source_metadata"]
    assert result["checks"]["high_confidence_has_multiple_sources"]


def test_case_2_low_confidence_reports_limitations():
    response = make_response(
        confidence="low",
        limitations=["Only limited evidence was available."],
    )

    result = evaluate_response(response)
    assert result["checks"]["has_limitations_when_confidence_is_low"]


def test_case_3_high_confidence_without_sources_fails():
    response = make_response(confidence="high")

    result = evaluate_response(response)
    assert not result["checks"]["high_confidence_has_multiple_sources"]


def test_case_4_empty_answer_fails():
    response = make_response(short_answer="")

    result = evaluate_response(response)
    assert not result["checks"]["has_short_answer"]


def test_case_5_missing_low_confidence_limitations_fails():
    response = make_response(
        confidence="low",
        limitations=[],
    )

    result = evaluate_response(response)
    assert not result["checks"]["has_limitations_when_confidence_is_low"]
