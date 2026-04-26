<div align="center">

<img src="https://img.shields.io/badge/Powered%20by-Claude%20AI-7c6dfa?style=for-the-badge&logo=anthropic&logoColor=white"/>
<img src="https://img.shields.io/badge/Platform-Amazon%20India-FF9900?style=for-the-badge&logo=amazon&logoColor=white"/>
<img src="https://img.shields.io/badge/Backend-FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white"/>
<img src="https://img.shields.io/badge/Deploy-Render-46E3B7?style=for-the-badge&logo=render&logoColor=white"/>
<img src="https://img.shields.io/badge/Frontend-GitHub%20Pages-222?style=for-the-badge&logo=github&logoColor=white"/>

<br/><br/>

# SellerPilot AI

### Autonomous AI Agent for Indian Amazon Sellers

**Real-time streaming · 5 intelligent tools · Voice-enabled UI · Agency-agents architecture**

<br/>

[**🚀 Live Demo**](https://adityasharma4287.github.io/AI-Agents/) &nbsp;·&nbsp;
[**📡 API Docs**](https://ai-agents-bnvj.onrender.com/docs) &nbsp;·&nbsp;
[**⚡ Quick Start**](#-quick-start)

<br/>

</div>

---

## Overview

SellerPilot AI is a production-ready autonomous agent that monitors and optimizes your Amazon India store in real time. Ask questions in plain Hindi or English — the agent thinks, selects the right tool, executes it, and streams results back character-by-character, exactly like Claude.

```
"Check my inventory"          →  Scans all products, flags critical stock, sends WhatsApp alert
"Pause wasteful ad campaigns" →  Analyzes ACOS, auto-pauses high spenders, calculates ₹ savings
"Reply to negative reviews"   →  Drafts professional Hinglish replies, waits for your approval
"Full store health report"    →  Revenue · Profit · ACOS · Alerts — complete daily audit
```

---

## Quick Start

**Prerequisites:** Python 3.10+, an [Anthropic API key](https://console.anthropic.com)

```bash
# 1. Clone
git clone https://github.com/adityasharma4287/AI-Agents.git
cd AI-Agents

# 2. Install dependencies
cd backend && pip install -r requirements.txt

# 3. Configure environment
cp ../env.example .env
# Add your key → ANTHROPIC_API_KEY=sk-ant-...

# 4. Start the server
uvicorn main:app --reload
```

Open **http://localhost:8000/docs** for the API explorer, or open `index.html` directly in your browser for the full dashboard.

> **Mock mode:** Set `ENVIRONMENT=development` to use built-in test data — no Amazon credentials needed.

---

## Features

### AI Agent Core
| Capability | Details |
|------------|---------|
| **Streaming** | SSE-based real-time response, character by character |
| **Tool use** | Multi-round tool calls per session — agent decides what to run |
| **Language** | Hinglish (Hindi + English) — natural for Indian sellers |
| **Circuit breaker** | Hard cap at 15 tool calls/session to control API cost |
| **Session memory** | Agent remembers context within a session |
| **Offline mode** | Full mock data set for development and demos |

### 5 Intelligent Tools
| Tool | What It Does |
|------|-------------|
| `check_inventory` | Stock levels, days remaining, restock quantity, WhatsApp alert |
| `optimize_ads` | ACOS analysis, auto-pause campaigns above threshold, ₹ savings |
| `monitor_reviews` | Fetch 1–3★ reviews, draft Hinglish replies, approval required |
| `check_listings` | Detect suppressed listings, buy box loss, exact fix steps |
| `store_health_report` | Full daily audit — revenue, profit, ad spend, all alerts |

### Dashboard Pages
- **Dashboard** — Revenue vs Ad Spend chart, action items, inventory/ad/health snapshots
- **AI Agent** — Chat interface with streaming, quick-chips, thinking blocks, tool logs
- **Inventory** — All products with stock bars, buy box %, rating, status
- **Ad Campaigns** — ACOS per campaign, pause/resume controls, daily waste in ₹
- **Reviews** — Star ratings, AI-drafted replies, one-click approve
- **Alerts** — Prioritized alert feed with severity levels
- **Orchestrator** — 5-step quality-gated pipeline, circuit breaker, memory log

### UI / UX (v3.2)
- **Voice (Text-to-Speech)** — click any element to hear it read aloud; hover 1.5s for preview
- **Aurora background** — animated particle canvas with meteor shower
- **Glassmorphism** — blur-backed cards, sidebar, and input area
- **Live counters** — revenue updates every 4 seconds, IST clock, ACOS fluctuation
- **Global search** — `Ctrl+K` to jump to any page or run any tool instantly
- **Keyboard nav** — `D` Dashboard · `A` Agent · `I` Inventory · `R` Reviews · `W` Workflow
- **Micro-animations** — count-up numbers, sparkle on hover, confetti on Run All, ripple clicks

---

## Project Structure

```
AI-Agents/
├── index.html                    # Dashboard UI (v3.2)
├── sellerpilot_agent.html        # Standalone chat UI
├── config.js                     # Backend URL config
├── env.example                   # Environment variable template
│
├── backend/
│   ├── main.py                   # FastAPI app + SSE endpoints
│   ├── core.py                   # Claude agent + circuit breaker + session memory
│   ├── tool_executor.py          # Tool dispatch logic
│   ├── tool_definitions.py       # Tool schemas (Claude function definitions)
│   ├── amazon_connector.py       # Amazon SP-API connector
│   ├── mock_data.py              # Dev/demo data
│   ├── notifications.py          # Twilio WhatsApp alerts
│   └── requirements.txt
│
└── .github/workflows/
    └── static.yml                # GitHub Pages auto-deploy
```

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `GET` | `/dashboard` | Store summary + account health |
| `GET` | `/inventory` | All products + low stock count |
| `GET` | `/ads` | All campaigns + high ACOS count |
| `GET` | `/reviews` | All reviews + negative count |
| `GET` | `/alerts` | Store alerts + unread count |
| `POST` | `/chat/stream` | **AI chat — SSE streaming** ⭐ |
| `POST` | `/chat` | AI chat — single response |
| `POST` | `/chat/clear` | Clear session history |
| `GET` | `/session/{id}/summary` | Session memory + tool call log |

**Example — streaming chat:**
```bash
curl -X POST https://ai-agents-bnvj.onrender.com/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"message": "Check my inventory and flag critical items", "session_id": "demo"}'
```

---

## Configuration

| Variable | Required | Description |
|----------|:--------:|-------------|
| `ANTHROPIC_API_KEY` | ✅ | Get from [console.anthropic.com](https://console.anthropic.com) |
| `ENVIRONMENT` | ✅ | `development` (mock) or `production` (real Amazon) |
| `TWILIO_ACCOUNT_SID` | ☐ | For WhatsApp alerts |
| `TWILIO_AUTH_TOKEN` | ☐ | For WhatsApp alerts |
| `TWILIO_WHATSAPP_FROM` | ☐ | Twilio sandbox number |
| `SELLER_WHATSAPP` | ☐ | Your number e.g. `+919XXXXXXXXX` |

---

## Deployment

### Backend → Render

| Setting | Value |
|---------|-------|
| Root Directory | `backend` |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `uvicorn main:app --host 0.0.0.0 --port $PORT` |
| Runtime | Python 3 |

Add `ANTHROPIC_API_KEY` in Render's **Environment** tab, then deploy.

> **Note:** Free tier instances sleep after inactivity — first request may take ~50 seconds to wake.  
> **Build fix:** If the build fails on `pydantic`, pin it to `pydantic==2.10.6` in `requirements.txt`.

### Frontend → GitHub Pages

Push to `main` — GitHub Actions (`.github/workflows/static.yml`) deploys automatically to:  
`https://adityasharma4287.github.io/AI-Agents/`

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| AI | Anthropic Claude `claude-sonnet-4-20250514` |
| Backend | Python · FastAPI · Uvicorn |
| Streaming | Server-Sent Events (SSE) |
| Frontend | HTML · CSS · Vanilla JS · Chart.js |
| Voice | Web Speech API |
| Visual FX | Canvas API (aurora · particles · meteors) |
| Alerts | Twilio WhatsApp API |
| Backend hosting | Render.com |
| Frontend hosting | GitHub Pages |

---

## Security

- Never commit `.env` — it is listed in `.gitignore`
- Store `ANTHROPIC_API_KEY` only in Render's environment variables
- Set `ENVIRONMENT=production` before going live
- Review replies require **manual seller approval** — no autonomous posting to Amazon

---

## License

MIT — free to use, modify, and distribute.

---

<div align="center">
<sub>Built with ❤️ for Indian Amazon sellers · Made by **Aditya Sharma**</sub>

<sub> <img width="498" height="280" alt="AnthemGIF (2)" src="https://github.com/user-attachments/assets/1126c235-40b3-47d5-9bae-0a2f4fa11cc5" />
MADE IN INDIA </sub>
</div>
