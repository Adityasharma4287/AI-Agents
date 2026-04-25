# SellerPilot AI 🤖

**Autonomous AI Agent for Indian Amazon Sellers — Powered by Anthropic Claude**

> Hindi + English (Hinglish) mein baat karta hai · Real-time streaming · Agency-agents patterns

---

## 🌐 Live Demo

| Service | URL |
|---------|-----|
| **Frontend** | GitHub Pages (`.github/workflows/static.yml` se auto-deploy) |
| **Backend API** | `https://ai-agents-bnvj.onrender.com` |
| **API Docs** | `https://ai-agents-bnvj.onrender.com/docs` |

---

## ⚡ Quick Start

### 1. Clone & Setup
```bash
git clone https://github.com/YOUR_USERNAME/AI-Agents.git
cd AI-Agents/backend
pip install -r requirements.txt
```

### 2. API Key Setup
```bash
cp .env.example .env
```
`.env` file mein apni Anthropic key daalo:
```
ANTHROPIC_API_KEY=sk-ant-your_key_here
```
👉 Key yahan milegi: **[console.anthropic.com](https://console.anthropic.com)**

### 3. Run
```bash
cd backend
uvicorn main:app --reload
```
Browser mein kholo: **http://localhost:8000/docs**

Frontend ke liye seedha `index.html` browser mein open karo.

---

## 📁 Project Structure

```
AI-Agents/
├── index.html                   # Main dashboard UI (frontend)
├── sellerpilot_agent.html       # Standalone chat UI
├── config.js                    # Frontend config (backend URL)
├── env.example                  # Environment variables template
├── gitignore                    # Secret files blocked
│
├── backend/
│   ├── main.py                  # FastAPI server — entry point
│   ├── core.py                  # AI Agent (Claude powered) + Circuit Breaker + Memory
│   ├── amazon_connector.py      # Amazon SP-API data connector
│   ├── mock_data.py             # Test data (development mode)
│   ├── tool_definitions.py      # Agent tools schema (5 tools)
│   ├── tool_executor.py         # Tool execution logic
│   ├── notifications.py         # WhatsApp alerts (Twilio)
│   └── requirements.txt         # Python packages
│
└── .github/
    └── workflows/
        └── static.yml           # GitHub Pages auto-deploy
```

---

## 🛠️ Features

### 🤖 AI Agent (Claude Powered)
- **Real-time SSE streaming** — response character-by-character dikhti hai
- **Multi-round tool use** — ek sawaal pe multiple tools chalata hai
- **Hinglish communication** — Indian sellers ke liye natural language
- **Circuit Breaker** — max 15 tool calls/session, cost control
- **Agent Memory** — session ke andar context yaad rakhta hai
- **Mock mode** — bina API key ke bhi kaam karta hai (testing)

### 📦 Inventory Monitor
- Har product ka stock level check karta hai
- Critical (< 5 units), Warning (below reorder point), OK — teeno levels detect karta hai
- Days remaining estimate karta hai
- Restock quantity recommend karta hai
- WhatsApp pe urgent alert bhejta hai

### 📢 Ad Optimizer
- Saare Sponsored Products aur Sponsored Brand campaigns analyze karta hai
- ACOS threshold (default 40%) se upar wale campaigns auto-pause karta hai
- Daily aur monthly rupee savings calculate karta hai
- High-performing campaigns identify karta hai (scale karne ke liye)

### ⭐ Review Manager
- 1–3 star unanswered reviews fetch karta hai
- Har review ke liye professional Hinglish reply draft karta hai
- **Seller approval ke baad hi post hota hai** — autonomous posting nahi

### 🏷️ Listing Health
- Suppressed listings detect karta hai (zero revenue wali)
- Buy Box loss identify karta hai
- Exact fix steps deta hai (image size, title length, pricing)

### 📊 Daily Health Report
- Complete store audit: revenue, profit, ad spend, ACOS
- Inventory status + suppressed listings + unanswered reviews
- Actions priority ke saath — sabse bade rupee impact wala pehle

### 🎛️ Orchestrator Pipeline
- Quality-gated workflow — ek tool ka result check hone ke baad agla chalta hai
- 5-step pipeline: Health Report → Inventory → Listings → Reviews → Ads
- Circuit Breaker dashboard with live call count

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Server status |
| `GET` | `/health` | Health check |
| `GET` | `/dashboard` | Store summary + account health |
| `GET` | `/inventory` | All products + low stock count |
| `GET` | `/ads` | All campaigns + high ACOS count |
| `GET` | `/reviews` | All reviews + negative count |
| `GET` | `/alerts` | Store alerts + unread count |
| `POST` | `/chat` | AI chat (non-streaming) |
| `POST` | `/chat/stream` | AI chat (SSE streaming) ⭐ |
| `POST` | `/chat/clear` | Clear session history |
| `GET` | `/session/{id}/summary` | Session memory + tool call log |

### Chat API Example
```bash
curl -X POST https://ai-agents-bnvj.onrender.com/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"message": "Check my inventory", "session_id": "my-session"}'
```

---

## 🔑 Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | ✅ Yes | Claude API key — `console.anthropic.com` |
| `ENVIRONMENT` | ✅ Yes | `development` = mock data · `production` = real Amazon |
| `TWILIO_ACCOUNT_SID` | ❌ Optional | WhatsApp alerts ke liye |
| `TWILIO_AUTH_TOKEN` | ❌ Optional | WhatsApp alerts ke liye |
| `TWILIO_WHATSAPP_FROM` | ❌ Optional | Twilio sandbox number |
| `SELLER_WHATSAPP` | ❌ Optional | Aapka WhatsApp number (`+91XXXXXXXXXX`) |

---

## 🧰 Tech Stack

| Layer | Technology |
|-------|-----------|
| **AI Model** | Anthropic Claude (`claude-sonnet-4-20250514`) |
| **Backend** | Python · FastAPI · Uvicorn |
| **Streaming** | Server-Sent Events (SSE) |
| **Frontend** | Vanilla HTML/CSS/JS · Chart.js |
| **Notifications** | Twilio WhatsApp API |
| **Hosting (Backend)** | Render.com |
| **Hosting (Frontend)** | GitHub Pages |

---

## 🚀 Deploy on Render

1. Render.com pe jaao → **New Web Service**
2. GitHub repo connect karo
3. Yeh settings karo:

| Setting | Value |
|---------|-------|
| **Root Directory** | `backend` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `uvicorn main:app --host 0.0.0.0 --port $PORT` |
| **Environment** | `Python 3` |

4. **Environment Variables** mein `ANTHROPIC_API_KEY` daalo
5. Deploy karo ✅

> ⚠️ Free instance 50 seconds tak spin-up time leta hai pehli request pe.

---

## 🤖 Agent Tools (5 Total)

```python
check_inventory(threshold_multiplier=1.0)
# Stock levels, days remaining, restock recommendations

optimize_ads(acos_threshold=40.0)
# ACOS analysis, auto-pause wasteful campaigns, savings in ₹

monitor_reviews(days_back=7)
# Negative reviews fetch, draft replies (approval required)

check_listings()
# Suppressed listings, buy box loss, fix steps

store_health_report()
# Complete daily audit, priority action list
```

---

## 💬 Example Queries

```
"Check all inventory — flag low stock"
"Pause all ad campaigns with ACOS above 40%"
"Find negative reviews and draft professional replies"
"Check listings for suppressed and buy box issues"
"Give me a complete store health report for today"
"What is the single most urgent issue right now?"
"How much money am I wasting on ads today?"
"Which product has the worst performance this week?"
```

---

## ⚠️ Important Security Notes

- **Never push `.env` to GitHub** — API keys expose nahi honi chahiye
- `.gitignore` already `.env` ko block karta hai
- `ANTHROPIC_API_KEY` sirf Render environment variables mein daalo
- Production mein `ENVIRONMENT=production` set karo

---

## 📄 License

MIT License — Free to use and modify.
