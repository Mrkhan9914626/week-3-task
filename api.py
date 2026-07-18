import json
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from agent import run_agent, run_agent_streamed


# ── Request / Response Models ───────────────────────────────────────────────


class AgentQuery(BaseModel):
    query: str
    max_turns: int = 15


class AgentResponse(BaseModel):
    output: str


class HealthResponse(BaseModel):
    status: str


# ── App Lifecycle ────────────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown — placeholder for future resource mgmt."""
    yield


app = FastAPI(
    title="Multi-Tool Agent API",
    description="Backend for the Week 3 Multi-Tool Agent using OpenAI Agents SDK + Gemini",
    version="0.1.0",
    lifespan=lifespan,
)

# Allow Streamlit (localhost:8501) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Endpoints ────────────────────────────────────────────────────────────────


@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint."""
    return HealthResponse(status="ok")


@app.post("/agent/run", response_model=AgentResponse)
async def agent_run(body: AgentQuery):
    """
    Run the multi-tool agent with a query and return the final answer.

    Use this endpoint for simple request-response mode.
    """
    try:
        output = await run_agent(body.query, max_turns=body.max_turns)
        return AgentResponse(output=output)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")


@app.get("/agent/stream")
async def agent_stream(
    query: str = Query(..., description="User query"),
    max_turns: int = Query(15, description="Max LLM-tool cycles"),
):
    """
    Stream agent execution events via Server-Sent Events.

    Event types:
    - `tool_call`: Agent is calling a tool
    - `tool_output`: Tool returned a result
    - `final_output`: The agent's final answer (partial or complete)
    - `error`: An error occurred
    """

    async def event_generator():
        try:
            async for event in run_agent_streamed(query, max_turns=max_turns):
                yield f"data: {json.dumps(event)}\n\n"
                await asyncio.sleep(0)  # yield control
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'detail': str(e)})}\n\n"
        finally:
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ── Run ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
