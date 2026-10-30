
from fastapi import FastAPI, HTTPException

from app.agent import run_research
from app.evaluator import evaluate_response
from app.schemas import ResearchRequest, ResearchResponse
from fastapi.middleware.cors import CORSMiddleware
app = FastAPI(
    title="Predixion AI Research Agent",
    description=(
        "A production-minded research agent with planning, "
        "web tools, structured answers, and failure handling."
    ),
    version="1.0.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
    "http://localhost:5173",
    "https://predixion-ai-research-agent.vercel.app",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)

@app.get("/")
async def root():
    return {
        "message": "Predixion AI Research Agent API",
        "status": "running",
    }


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.post("/research", response_model=ResearchResponse)
async def research(request: ResearchRequest):
    try:
        return await run_research(request.question)
    except Exception as exc:
        # Keep internal details out of client-facing errors.
        raise HTTPException(
            status_code=500,
            detail="The research workflow encountered an unexpected error.",
        ) from exc

@app.post("/evaluate")
async def evaluate(request: ResearchRequest):
    try:
        response = await run_research(request.question)
        return evaluate_response(response)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="The evaluation workflow encountered an unexpected error.",
        ) from exc
