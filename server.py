"""
FastAPI backend for ReAct Agent
Run: uvicorn server:app --reload --port 8000
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import json, sys, os
from pathlib import Path
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))

try:
    from agents.planner_agent import PlannerAgent
    from agents.critic_agent import CriticAgent
    from memory.learning_memory import LearningMemory
    from memory.working_memory import WorkingMemory
    from core.react_loop import ReActLoop, _is_bad_answer
    from tools.web_search_tool import WebSearchTool
    from tools.python_tool import PythonTool
    from tools.wiki_tool import WikiTool

    planner               = PlannerAgent()
    critic                = CriticAgent()
    learning_memory       = LearningMemory()
    shared_working_memory = WorkingMemory()
    tools                 = [WikiTool(), WebSearchTool(), PythonTool()]
    agent                 = ReActLoop(tools, shared_working_memory, learning_memory)

    AGENT_READY = True
    print("✅ Agent loaded successfully.")

except Exception as e:
    print(f"[WARN] Agent not loaded: {e}")
    import traceback; traceback.print_exc()
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


@app.get("/")
def serve_ui():
    if os.path.exists("index.html"):
        return FileResponse("index.html")
    return {"message": "ReAct Agent API running."}


class QueryRequest(BaseModel):
    query: str

class DeleteMemoryRequest(BaseModel):
    query: str


@app.get("/health")
def health():
    return {"status": "ok", "agent_ready": AGENT_READY}


@app.post("/query")
def query_endpoint(req: QueryRequest):
    query = req.query.strip()
    if not query:
        raise HTTPException(400, "Query cannot be empty")

    if not AGENT_READY:
        return _stub(query)

    # Only serve from memory if it's a good cached answer
    learned = learning_memory.retrieve(query)
    if learned and not _is_bad_answer(learned):
        _log(query, True, False, 1, 0, 0)
        return {
            "answer":  learned,
            "plan":    "Retrieved from learned memory.",
            "source":  "learned",
            "valid":   True,
            "metrics": {"steps":1,"tool_calls":0,"tokens":0,"success":True,"hallucination":False},
        }

    agent.metrics.reset()

    try:
        plan_text, _ = planner.plan(query)
    except Exception:
        plan_text = ""

    answer = agent.run(query)
    valid  = critic.verify(query, answer)
    m      = agent.metrics

    # ✅ NEVER cache bad/empty answers
    if valid and not _is_bad_answer(answer):
        learning_memory.store(query, answer)
        m.mark_success()
    elif _is_bad_answer(answer):
        print(f"[Server] Not caching bad answer: {answer}")
        valid = False
        m.mark_hallucination()
    else:
        m.mark_hallucination()

    _log(query, m.success, m.hallucination, m.steps, m.tool_calls, m.tokens)

    return {
        "answer":  answer,
        "plan":    plan_text,
        "source":  "agent",
        "valid":   valid,
        "metrics": {
            "steps":         m.steps,
            "tool_calls":    m.tool_calls,
            "tokens":        m.tokens,
            "success":       m.success,
            "hallucination": m.hallucination,
        },
    }


@app.get("/metrics")
def get_metrics():
    data = json.loads(METRICS_FILE.read_text())
    if not data:
        return {"total":0,"success_rate":0,"hallucination_rate":0,
                "avg_steps":0,"avg_tools":0,"avg_tokens":0,"runs":[]}
    total = len(data)
    return {
        "total":              total,
        "success_rate":       round(sum(d["success"]         for d in data)/total*100, 1),
        "hallucination_rate": round(sum(d["hallucination"]   for d in data)/total*100, 1),
        "avg_steps":          round(sum(d["reasoning_steps"] for d in data)/total, 2),
        "avg_tools":          round(sum(d["tool_calls"]      for d in data)/total, 2),
        "avg_tokens":         round(sum(d["token_usage"]     for d in data)/total, 1),
        "runs":               data[-50:],
    }

@app.delete("/metrics")
def clear_metrics():
    METRICS_FILE.write_text("[]")
    return {"message": "Metrics cleared."}


@app.get("/memory")
def get_memory():
    if not AGENT_READY:
        return {"entries": []}
    return {"entries": learning_memory.all_entries()}

@app.delete("/memory")
def clear_all_memory():
    learning_memory.clear_all()
    return {"message": "All memory cleared."}

@app.delete("/memory/entry")
def delete_memory_entry(req: DeleteMemoryRequest):
    deleted = learning_memory.delete(req.query)
    if not deleted:
        raise HTTPException(404, "Entry not found")
    return {"message": f"Deleted: {req.query}"}


@app.get("/history/search")
def search_history(q: str = ""):
    data = json.loads(METRICS_FILE.read_text())
    if not q.strip():
        return {"runs": data[-50:]}
    filtered = [r for r in data if q.lower() in r.get("query","").lower()]
    return {"runs": filtered[-50:]}


@app.post("/reset-context")
def reset_context():
    if AGENT_READY:
        shared_working_memory.conv_log = []
    return {"message": "Conversation context cleared."}


def _stub(query):
    return {
        "answer":  f"[STUB] {query}",
        "plan":    "Agent not loaded.",
        "source":  "stub",
        "valid":   True,
        "metrics": {"steps":1,"tool_calls":0,"tokens":0,"success":True,"hallucination":False},
    }

def _log(query, success, hallucination, steps, tools_used, tokens):
    data = json.loads(METRICS_FILE.read_text())
    data.append({
        "time":            str(datetime.now()),
        "query":           query,
        "success":         success,
        "hallucination":   hallucination,
        "reasoning_steps": steps,
        "tool_calls":      tools_used,
        "token_usage":     tokens,
    })
    METRICS_FILE.write_text(json.dumps(data, indent=2))
