# backend/main.py
# ============================================================
# YEH FILE: Server ka main entry point
# FastAPI = Python ka modern, fast web framework
# Yeh sab API endpoints define karta hai jo frontend use karega
# ============================================================

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler

from models.database import create_tables, get_db, SessionLocal, Alert, AgentAction
from tools.amazon_connector import amazon
from agent.sellerpilot_agent import agent

# ============================================================
# APP SETUP
# ============================================================
app = FastAPI(
    title="SellerPilot AI",
    description="AI Agent for Amazon Sellers - India",
    version="1.0.0"
)

# CORS - Frontend ko backend se baat karne deta hai
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# SCHEDULER - Har ghante automatically run hoga agent
# ============================================================
scheduler = BackgroundScheduler()


def run_scheduled_check():
    """Har ghante background mein run hoga"""
    print(f"\n⏰ Scheduled check at {datetime.now().strftime('%H:%M')}")
    try:
        result = agent.run("Check inventory levels and alert for low stock")
        agent.run("Optimize ad campaigns - pause high ACOS campaigns")
        print("✅ Scheduled check complete")
    except Exception as e:
        print(f"❌ Scheduled check failed: {e}")


def run_daily_morning_routine():
    """Subah 9 baje complete routine"""
    print("\n🌅 Running daily morning routine...")
    agent.run_daily_routine()


# ============================================================
# STARTUP & SHUTDOWN
# ============================================================
@app.on_event("startup")
async def startup():
    create_tables()  # Database tables banao
    scheduler.add_job(run_scheduled_check, "interval", hours=1, id="hourly_check")
    scheduler.add_job(run_daily_morning_routine, "cron", hour=9, minute=0, id="daily_routine")
    scheduler.start()
    print("SellerPilot AI Server started!")
    print("Dashboard: http://localhost:8000/docs")


@app.on_event("shutdown")
async def shutdown():
    scheduler.shutdown()


# ============================================================
# REQUEST/RESPONSE MODELS
# ============================================================
class AgentTaskRequest(BaseModel):
    task: str
    run_all: bool = False

class ApproveActionRequest(BaseModel):
    action_id: int
    approved: bool
    seller_note: Optional[str] = None


# ============================================================
# API ENDPOINTS
# ============================================================

# Root
@app.get("/")
def root():
    return {
        "name": "SellerPilot AI",
        "status": "running",
        "version": "1.0.0",
        "endpoints": ["/dashboard", "/agent/run", "/inventory", "/reviews", "/ads", "/alerts"]
    }


# ── DASHBOARD ────────────────────────────────────────────────
@app.get("/dashboard")
def get_dashboard():
    """Main dashboard data - sab kuch ek jagah"""
    summary = amazon.get_dashboard_summary()
    account_health = amazon.get_account_health()
    return {
        "summary": summary,
        "account_health": account_health,
        "timestamp": datetime.now().isoformat()
    }


# ── AGENT ────────────────────────────────────────────────────
@app.post("/agent/run")
async def run_agent_task(request: AgentTaskRequest, background_tasks: BackgroundTasks):
    """Agent ko manually ek task do"""
    if not request.task:
        raise HTTPException(status_code=400, detail="Task cannot be empty")

    if request.run_all:
        result = agent.run_daily_routine()
    else:
        result = agent.run(request.task)

    return result


@app.post("/agent/daily-routine")
async def trigger_daily_routine(background_tasks: BackgroundTasks):
    """Daily routine manually trigger karo"""
    background_tasks.add_task(agent.run_daily_routine)
    return {"message": "Daily routine started in background. Check logs for progress."}


# ── INVENTORY ────────────────────────────────────────────────
@app.get("/inventory")
def get_inventory():
    """All products aur stock levels"""
    products = amazon.get_inventory()
    low_stock = [p for p in products if p["current_stock"] <= p["reorder_point"]]
    return {
        "total": len(products),
        "low_stock_count": len(low_stock),
        "products": products
    }


@app.post("/inventory/check-now")
async def check_inventory_now():
    """Abhi inventory check karo"""
    result = agent.run("Check all inventory levels and send alerts for low stock products")
    return result


# ── REVIEWS ──────────────────────────────────────────────────
@app.get("/reviews")
def get_reviews():
    """All reviews"""
    reviews = amazon.get_reviews()
    negative = [r for r in reviews if r["rating"] <= 2]
    return {
        "total": len(reviews),
        "negative_count": len(negative),
        "reviews": reviews
    }


@app.post("/reviews/monitor-now")
async def monitor_reviews_now():
    """Abhi reviews check karo aur replies draft karo"""
    result = agent.run("Monitor all reviews and draft professional replies for negative ones")
    return result


# ── ADS ──────────────────────────────────────────────────────
@app.get("/ads")
def get_ads():
    """All ad campaigns"""
    campaigns = amazon.get_ad_performance()
    high_acos = [c for c in campaigns if c["acos"] > 40]
    return {
        "total_campaigns": len(campaigns),
        "high_acos_count": len(high_acos),
        "campaigns": campaigns
    }


@app.post("/ads/optimize-now")
async def optimize_ads_now():
    """Abhi ads optimize karo"""
    result = agent.run("Analyze all ad campaigns and pause those with ACOS above 40%")
    return result


# ── ALERTS ───────────────────────────────────────────────────
@app.get("/alerts")
def get_alerts():
    """Agent ke recent actions aur alerts"""
    # Mock alerts - production mein DB se aayenge
    alerts = [
        {
            "id": 1,
            "type": "low_stock",
            "severity": "critical",
            "message": "ASIN B08N5WRWNW: Only 8 units left (reorder point: 20)",
            "asin": "B08N5WRWNW",
            "is_read": False,
            "created_at": datetime.now().isoformat()
        },
        {
            "id": 2,
            "type": "listing_suppressed",
            "severity": "high",
            "message": "Wireless Earbuds listing is suppressed on Amazon",
            "asin": "B07XQXZABC",
            "is_read": False,
            "created_at": datetime.now().isoformat()
        },
        {
            "id": 3,
            "type": "high_acos",
            "severity": "high",
            "message": "Campaign 'Earbuds - Auto' ACOS at 145% - paused automatically",
            "is_read": True,
            "created_at": datetime.now().isoformat()
        }
    ]
    return {"alerts": alerts, "unread_count": len([a for a in alerts if not a["is_read"]])}


# ── HEALTH CHECK ─────────────────────────────────────────────
@app.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
