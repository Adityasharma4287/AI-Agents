# main.py
# SellerPilot AI — FastAPI Server (Groq powered)

import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from datetime import datetime

from core import agent
from amazon_connector import amazon

app = FastAPI(title="SellerPilot AI", version="3.1.0", docs_url="/docs")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"

class ClearRequest(BaseModel):
    session_id: str = "default"


# ── CORE ROUTES ───────────────────────────────────────────────
@app.get("/")
def root():
    return {"name": "SellerPilot AI", "version": "3.1.0", "status": "running"}

@app.get("/health")
def health():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

@app.get("/dashboard")
def dashboard():
    return {
        "summary": amazon.get_dashboard_summary(),
        "account_health": amazon.get_account_health(),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/inventory")
def get_inventory():
    products = amazon.get_inventory()
    low = [p for p in products if p["current_stock"] <= p["reorder_point"]]
    sup = [p for p in products if p["status"] == "suppressed"]
    return {"products": products, "total": len(products),
            "low_stock_count": len(low), "suppressed_count": len(sup)}

@app.get("/ads")
def get_ads():
    campaigns = amazon.get_ad_campaigns()
    high_acos = [c for c in campaigns if c["acos"] > 40]
    total_spend = sum(c["spend"] for c in campaigns)
    wasted = sum(c["spend"] for c in high_acos)
    return {"campaigns": campaigns, "total": len(campaigns),
            "high_acos_count": len(high_acos),
            "total_spend": round(total_spend, 2),
            "wasted_spend": round(wasted, 2)}

@app.get("/reviews")
def get_reviews():
    reviews = amazon.get_reviews(unanswered_only=False)
    negative = [r for r in reviews if r["rating"] <= 2]
    return {"reviews": reviews, "total": len(reviews), "negative_count": len(negative)}

@app.get("/alerts")
def get_alerts():
    alerts = [
        {"id": 1, "type": "low_stock", "severity": "critical",
         "message": "ASIN B08N5WRWNW: Only 8 units left (reorder point: 20)",
         "asin": "B08N5WRWNW", "is_read": False, "created_at": datetime.now().isoformat()},
        {"id": 2, "type": "listing_suppressed", "severity": "high",
         "message": "Wireless Earbuds listing is suppressed on Amazon",
         "asin": "B07XQXZABC", "is_read": False, "created_at": datetime.now().isoformat()},
        {"id": 3, "type": "high_acos", "severity": "high",
         "message": "Campaign 'Earbuds - Auto' ACOS at 145% - paused automatically",
         "is_read": True, "created_at": datetime.now().isoformat()},
    ]
    return {"alerts": alerts, "unread_count": len([a for a in alerts if not a["is_read"]])}


# ── CHAT ─────────────────────────────────────────────────────
@app.post("/chat")
def chat(req: ChatRequest):
    return agent.chat(req.message, req.session_id)

@app.post("/chat/stream")
def chat_stream(req: ChatRequest):
    def gen():
        for event in agent.chat_stream(req.message, req.session_id):
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"
    return StreamingResponse(gen(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

@app.post("/chat/clear")
def clear(req: ClearRequest):
    agent.clear_history(req.session_id)
    return {"cleared": True, "session_id": req.session_id}

@app.get("/session/{session_id}/summary")
def session_summary(session_id: str):
    return agent.get_session_summary(session_id)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
