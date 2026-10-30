
import asyncio
import logging

from langgraph.graph import StateGraph, START, END

from app.graph_state import ResearchState
from app.planner import create_plan
from app.schemas import ExecutionEvent, ResearchResponse, ResearchSource
from app.tools import (
    web_search,
    fetch_webpage,
    evaluate_source_quality,
)
from app.agent import synthesize

logger = logging.getLogger(__name__)


async def planning_node(state: ResearchState) -> dict:
    plan = create_plan(state["question"])

    return {
        "plan": plan,
        "trace": [
            ExecutionEvent(
                tool="planner",
                status="success",
                message=f"Created {len(plan.steps)} research steps.",
            )
        ],
        "limitations": [],
        "evidence": [],
        "sources": [],
    }


async def search_node(state: ResearchState) -> dict:
    trace = list(state.get("trace", []))
    limitations = list(state.get("limitations", []))

    try:
        result = await web_search(state["question"], max_results=5)
    except Exception as exc:
        logger.exception("Web search failed")
        result = {
            "success": False,
            "error": type(exc).__name__,
            "results": [],
        }

    if not result.get("success"):
        trace.append(
            ExecutionEvent(
                tool="web_search",
                status="failed",
                message=str(result.get("error", "Web search failed.")),
            )
        )
        limitations.append("Web search was unavailable.")
    else:
        trace.append(
            ExecutionEvent(
                tool="web_search",
                status="success",
                message=f"Retrieved {result.get('count', 0)} search results.",
            )
        )

    raw_results = result.get("results", [])
    candidates = []
    seen_urls = set()

    for item in raw_results:
        if not isinstance(item, dict):
            continue

        url = item.get("url")
        if not isinstance(url, str) or not url.strip():
            continue

        if url in seen_urls:
            continue

        seen_urls.add(url)
        candidates.append(item)

    valid_count = len(candidates)
    candidates = candidates[:3]

    trace.append(
        ExecutionEvent(
            tool="filter_sources",
            status="success",
            message=(
                f"Filtered {len(raw_results)} results; "
                f"{len(candidates)} unique sources selected "
                f"for retrieval."
            ),
        )
    )

    if not candidates:
        limitations.append("No valid unique search results were available.")

    return {
        "search_result": result,
        "candidates": candidates,
        "trace": trace,
        "limitations": limitations,
    }



async def fetch_node(state: ResearchState) -> dict:
    trace = list(state.get("trace", []))
    evidence = list(state.get("evidence", []))
    sources = list(state.get("sources", []))
    candidates = state.get("candidates", [])

    pages = await asyncio.gather(
        *(fetch_webpage(item["url"]) for item in candidates),
        return_exceptions=True,
    )

    for item, page in zip(candidates, pages):
        if isinstance(page, Exception) or not isinstance(page, dict):
            page = {"success": False}

        if not page.get("success"):
            trace.append(
                ExecutionEvent(
                    tool="fetch_webpage",
                    status="failed",
                    message=(f"Could not retrieve {item['url']}; "+ ("using search snippet as fallback."if item.get("snippet")else "no fallback snippet available."
                                )
                            ),
                )
            )

            snippet = item.get("snippet", "")
            if snippet:
                evidence.append(
                    {
                        "title": item.get("title", ""),
                        "url": item["url"],
                        "text": snippet,
                        "evidence_type": "search_snippet",
                    }
                )

                sources.append(
                    ResearchSource(
                        title=item.get("title", "Untitled source"),
                        url=item["url"],
                        snippet=snippet,
                    )
                )
            continue

        title = page.get("title") or item.get("title", "Untitled source")
        text = page.get("text", "")

        trace.append(
            ExecutionEvent(
                tool="fetch_webpage",
                status="success",
                message=f"Retrieved {title}.",
            )
        )

        if text.strip():
            evidence.append(
                {
                    "title": title,
                    "url": item["url"],
                    "text": text,
                    "evidence_type": "webpage",
                }
            )

            sources.append(
                ResearchSource(
                    title=title,
                    url=item["url"],
                    snippet=text[:500],
                )
            )

    return {
        "evidence": evidence,
        "sources": sources,
        "trace": trace,
    }


async def evaluate_node(state: ResearchState) -> dict:
    trace = list(state.get("trace", []))
    limitations = list(state.get("limitations", []))
    evidence = state.get("evidence", [])

    quality = evaluate_source_quality(state["question"], evidence)

    trace.append(
        ExecutionEvent(
            tool="evaluate_source_quality",
            status="success",
            message=(
                f"Quality: {quality['quality']}; "
                f"score: {quality['score']}; "
                f"unique sources: {quality['source_count']}."
            ),
        )
    )

    if quality["quality"] == "poor":
        limitations.append(
            "Source quality is poor; findings may be incomplete."
        )

    limitations.extend(quality.get("warnings", []))

    return {
        "quality_result": quality,
        "trace": trace,
        "limitations": list(dict.fromkeys(limitations)),
    }


async def synthesis_node(state: ResearchState) -> dict:
    question = state["question"]
    plan = state["plan"]
    trace = list(state.get("trace", []))
    limitations = list(state.get("limitations", []))
    evidence = state.get("evidence", [])
    sources = state.get("sources", [])
    quality = state.get("quality_result", {})

    if not evidence:
        response = ResearchResponse(
            user_question=question,
            plan=plan.steps,
            execution_trace=trace,
            short_answer="Insufficient evidence to answer this question.",
            key_findings=[],
            sources_used=[],
            confidence="low",
            assumptions=[],
            limitations=list(dict.fromkeys(
                limitations + ["No usable research evidence found."]
            )),
            suggested_next_steps=[
                "Check the search configuration and retry."
            ],
        )
        return {"response": response}

    try:
        result = await asyncio.to_thread(synthesize, question, evidence)

        selected_urls = set(result["used_source_urls"])
        selected_sources = [
            source for source in sources
            if str(source.url) in selected_urls
        ]

        confidence = result["confidence"]

        if quality.get("quality") == "poor":
            confidence = "low"
        elif quality.get("quality") == "moderate" and confidence == "high":
            confidence = "medium"

        if all(
            item.get("evidence_type") == "search_snippet"
            for item in evidence
        ):
            confidence = "low"
            limitations.append(
                "Only search snippets were available; webpage retrieval failed."
            )

        if not selected_sources:
            confidence = "low"
            limitations.append(
                "No source URL was validated against the synthesized answer."
            )
        elif len(selected_sources) < 2 and confidence == "high":
            confidence = "medium"

        trace.append(
            ExecutionEvent(
                tool="answer_synthesis",
                status="success",
                message="Gemini generated structured output.",
            )
        )

        response = ResearchResponse(
            user_question=question,
            plan=plan.steps,
            execution_trace=trace,
            short_answer=result["short_answer"],
            key_findings=result["key_findings"],
            sources_used=selected_sources,
            confidence=confidence,
            assumptions=result["assumptions"],
            limitations=list(dict.fromkeys(
                limitations + result["limitations"]
            )),
            suggested_next_steps=result["suggested_next_steps"],
        )

    except Exception as exc:
        logger.exception("Research answer synthesis failed")

        trace.append(
            ExecutionEvent(
                tool="answer_synthesis",
                status="failed",
                message=f"Synthesis failed: {type(exc).__name__}",
            )
        )

        response = ResearchResponse(
            user_question=question,
            plan=plan.steps,
            execution_trace=trace,
            short_answer=(
                "Research evidence was collected, but "
                "the final answer could not be generated."
            ),
            key_findings=[],
            sources_used=sources,
            confidence="low",
            assumptions=[],
            limitations=list(dict.fromkeys(
                limitations + [f"Synthesis failed: {type(exc).__name__}."]
            )),
            suggested_next_steps=[
                "Check the backend terminal and Gemini model availability."
            ],
        )

    return {"response": response}


def build_research_graph():
    graph = StateGraph(ResearchState)

    graph.add_node("plan", planning_node)
    graph.add_node("search", search_node)
    graph.add_node("fetch", fetch_node)
    graph.add_node("evaluate", evaluate_node)
    graph.add_node("synthesize", synthesis_node)

    graph.add_edge(START, "plan")
    graph.add_edge("plan", "search")
    graph.add_edge("search", "fetch")
    graph.add_edge("fetch", "evaluate")
    graph.add_edge("evaluate", "synthesize")
    graph.add_edge("synthesize", END)

    return graph.compile()
