
import pytest

from app.graph_workflow import build_research_graph


@pytest.mark.asyncio
async def test_graph_returns_structured_response(monkeypatch):
    from app import graph_workflow

    async def fake_search(question, max_results=5):
        return {
            "success": True,
            "count": 1,
            "results": [
                {
                    "title": "Example Research",
                    "url": "https://example.com/research",
                    "snippet": "Example evidence for testing research.",
                }
            ],
        }

    async def fake_fetch(url):
        return {
            "success": True,
            "title": "Example Research",
            "text": "Example evidence for testing research.",
        }

    def fake_quality(question, evidence):
        return {
            "quality": "good",
            "score": 0.9,
            "source_count": 1,
            "warnings": [],
        }

    def fake_synthesize(question, evidence):
        return {
            "short_answer": "This is a test answer.",
            "key_findings": ["Finding supported by test evidence."],
            "used_source_urls": ["https://example.com/research"],
            "confidence": "medium",
            "assumptions": [],
            "limitations": [],
            "suggested_next_steps": ["Verify with more sources."],
        }

    monkeypatch.setattr(graph_workflow, "web_search", fake_search)
    monkeypatch.setattr(graph_workflow, "fetch_webpage", fake_fetch)
    monkeypatch.setattr(
        graph_workflow, "evaluate_source_quality", fake_quality
    )
    monkeypatch.setattr(graph_workflow, "synthesize", fake_synthesize)

    graph = build_research_graph()
    result = await graph.ainvoke({
        "question": "Test research question",
    })

    response = result["response"]

    assert response.short_answer == "This is a test answer."
    assert response.confidence == "medium"
    assert len(response.plan) == 4
    assert any(
        event.tool == "evaluate_source_quality"
        for event in response.execution_trace
    )
    assert len(response.sources_used) == 1

@pytest.mark.asyncio
async def test_graph_handles_search_failure(monkeypatch):
    from app import graph_workflow

    async def fake_search(question, max_results=5):
        return {
            "success": False,
            "error": "Simulated search API failure",
            "results": [],
        }

    monkeypatch.setattr(graph_workflow, "web_search", fake_search)

    graph = build_research_graph()
    result = await graph.ainvoke({
        "question": "Test a search failure",
    })

    response = result["response"]

    assert response.confidence == "low"
    assert "Insufficient evidence" in response.short_answer
    assert any(
        event.tool == "web_search" and event.status == "failed"
        for event in response.execution_trace
    )
    assert any(
        "Web search was unavailable" in limitation
        for limitation in response.limitations
    )
