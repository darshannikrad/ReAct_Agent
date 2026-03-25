"""
FastAPI backend — bridges the React frontend with the existing agent pipeline.
Run with:  uvicorn server:app --reload --port 8000
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json, sys, os
from pathlib import Path
from datetime import datetime

# ── make sure your existing modules are importable ──────────────────────────
sys.path.insert(0, os.path.dirname(__file__))

# ── lazy imports so the server starts even if optional deps are missing ──────
try:
    from agents.planner_agent import PlannerAgent
    from agents.critic_agent import CriticAgent
    from memory.learning_memory import LearningMemory
    from memory.working_memory import WorkingMemory
    from core.react_loop import ReActLoop
    from tools.web_search_tool import WebSearchTool
    from tools.python_tool import PythonTool

    planner        = PlannerAgent()
    critic         = CriticAgent()
    learning_memory = LearningMemory()
    tools          = [WebSearchTool(), PythonTool()]
    AGENT_READY    = True
except Exception as e:
    print(f"[WARN] Agent modules not loaded: {e}")
    AGENT_READY = False

METRICS_FILE = Path("evaluation/run_metrics.json")
METRICS_FILE.parent.mkdir(parents=True, exist_ok=True)
if not METRICS_FILE.exists():
    METRICS_FILE.write_text("[]")

app = FastAPI(title="ReAct Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────── Schemas ────────────────────────────────────────

class QueryRequest(BaseModel):
    query: str


class QueryResponse(BaseModel):
    answer: str
    plan: str
    source: str          # "learned" | "agent"
    valid: bool
    metrics: dict


# ─────────────────────────── Routes ─────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "agent_ready": AGENT_READY}


@app.post("/query", response_model=QueryResponse)
def query_agent(req: QueryRequest):
    query = req.query.strip()
    if not query:
        raise HTTPException(400, "Query cannot be empty")

    if not AGENT_READY:
        # ── demo / stub mode ────────────────────────────────────────────────
        return QueryResponse(
            answer=f"[STUB] Echo: {query}",
            plan="1. Receive query\n2. Return stub answer",
            source="agent",
            valid=True,
            metrics={"steps": 1, "tool_calls": 0, "tokens": 0,
                     "success": True, "hallucination": False},
        )

    # ── learned memory shortcut ──────────────────────────────────────────────
    learned = learning_memory.retrieve(query)
    if learned:
        _append_metric(query, True, False, 1, 0, 0)
        return QueryResponse(
            answer=learned,
            plan="Retrieved from learned memory — no LLM call needed.",
            source="learned",
            valid=True,
            metrics={"steps": 1, "tool_calls": 0, "tokens": 0,
                     "success": True, "hallucination": False},
        )

    # ── fresh agent run ──────────────────────────────────────────────────────
    working_memory = WorkingMemory()
    agent = ReActLoop(tools, working_memory, learning_memory)

    plan_text, _ = planner.plan(query)

    answer = agent.run(query)

    valid = critic.verify(query, answer)

    m = agent.metrics
    if valid:
        learning_memory.store(query, answer)
        m.mark_success()
    else:
        m.mark_hallucination()

    metrics_dict = {
        "steps":        m.steps,
        "tool_calls":   m.tool_calls,
        "tokens":       m.tokens,
        "success":      m.success,
        "hallucination": m.hallucination,
    }

    m.save(query)

    return QueryResponse(
        answer=answer,
        plan=plan_text,
        source="agent",
        valid=valid,
        metrics=metrics_dict,
    )


@app.get("/metrics")
def get_metrics():
    data = json.loads(METRICS_FILE.read_text())
    if not data:
        return {"total": 0, "success_rate": 0, "hallucination_rate": 0,
                "avg_steps": 0, "avg_tools": 0, "avg_tokens": 0, "runs": []}
    total = len(data)
    return {
        "total":              total,
        "success_rate":       round(sum(d["success"]      for d in data) / total * 100, 1),
        "hallucination_rate": round(sum(d["hallucination"] for d in data) / total * 100, 1),
        "avg_steps":          round(sum(d["reasoning_steps"] for d in data) / total, 2),
        "avg_tools":          round(sum(d["tool_calls"]      for d in data) / total, 2),
        "avg_tokens":         round(sum(d["token_usage"]     for d in data) / total, 1),
        "runs":               data[-20:],   # last 20 for the chart
    }


@app.get("/memory")
def get_memory():
    try:
        from memory.learning_memory import LearningMemory
        lm = LearningMemory()
        return {"entries": [{"query": k, "answer": v} for k, v in lm.db.items()]}
    except Exception:
        return {"entries": []}


# ─────────────────────────── helpers ────────────────────────────────────────

def _append_metric(query, success, hallucination, steps, tools_used, tokens):
    data = json.loads(METRICS_FILE.read_text())
    data.append({
        "time": str(datetime.now()),
        "query": query,
        "success": success,
        "hallucination": hallucination,
        "reasoning_steps": steps,
        "tool_calls": tools_used,
        "token_usage": tokens,
    })
    METRICS_FILE.write_text(json.dumps(data, indent=2))
