# backend/main.py
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from agent.core import agent
from tools.amazon_connector import amazon

app = FastAPI(title="SellerPilot AI", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── MODELS ───────────────────────────────────────────────────
class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"

class ClearRequest(BaseModel):
    session_id: str = "default"


# ── ROUTES ───────────────────────────────────────────────────

@app.get("/")
def root():
    return {"name": "SellerPilot AI", "version": "2.0.0", "status": "running"}

@app.get("/health")
def health():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

@app.get("/dashboard")
def dashboard():
    return {
        "summary": amazon.get_dashboard_summary(),
        "account_health": amazon.get_account_health(),
        "timestamp": datetime.now().isoformat(),
    }

@app.get("/inventory")
def get_inventory():
    products = amazon.get_inventory()
    return {"products": products, "total": len(products)}

@app.get("/ads")
def get_ads():
    campaigns = amazon.get_ad_campaigns()
    return {"campaigns": campaigns, "total": len(campaigns)}

@app.get("/reviews")
def get_reviews():
    reviews = amazon.get_reviews(unanswered_only=False)
    return {"reviews": reviews, "total": len(reviews)}


# ── CHAT (non-streaming) ─────────────────────────────────────
@app.post("/chat")
def chat(req: ChatRequest):
    result = agent.chat(req.message, req.session_id)
    return result


# ── CHAT STREAM (SSE) ─────────────────────────────────────────
# This is the key endpoint — sends real-time events to frontend
# Frontend receives: thinking → tool_start → tool_result → text → done
@app.post("/chat/stream")
def chat_stream(req: ChatRequest):
    def event_generator():
        for event in agent.chat_stream(req.message, req.session_id):
            # SSE format: data: {json}\n\n
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# ── CLEAR HISTORY ────────────────────────────────────────────
@app.post("/chat/clear")
def clear(req: ClearRequest):
    agent.clear_history(req.session_id)
    return {"cleared": True, "session_id": req.session_id}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
