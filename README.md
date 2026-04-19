# SellerPilot AI — Complete Setup Guide

## Quick Start

```bash
# 1. Clone / download karo
cd sellerpilot2/backend

# 2. Virtual environment banao
python3 -m venv venv
source venv/bin/activate        # Mac/Linux
# venv\Scripts\activate         # Windows

# 3. Packages install karo
pip install -r requirements.txt

# 4. API key setup karo
cp .env.example .env
# .env kholo → ANTHROPIC_API_KEY daalo
# https://console.anthropic.com/keys se milega

# 5. Server start karo
python3 main.py
# → Server: http://localhost:8000

# 6. Frontend open karo
# frontend/index.html browser mein double-click karo
```

## Architecture

```
User types → frontend/index.html
    ↓ POST /chat/stream (SSE)
backend/main.py (FastAPI)
    ↓
backend/agent/core.py
    ↓ Claude API (claude-sonnet-4-6) + tools
    ↓ Claude decides which tool to call
backend/agent/tool_executor.py
    ↓ Runs the actual tool
backend/tools/amazon_connector.py
    ↓ Amazon SP-API (or mock data)
    → Result back to Claude
    → Claude writes final answer
    → SSE stream to frontend
    → Real-time display
```

## Files

| File | Purpose |
|------|---------|
| `frontend/index.html` | Complete chat UI (Claude-style) |
| `backend/main.py` | FastAPI server + SSE endpoint |
| `backend/agent/core.py` | Claude API tool_use loop |
| `backend/agent/tool_definitions.py` | Tool schemas for Claude |
| `backend/agent/tool_executor.py` | Actual tool logic |
| `backend/tools/amazon_connector.py` | Amazon data fetcher |
| `backend/tools/mock_data.py` | Realistic test data |
| `backend/utils/notifications.py` | WhatsApp alerts |

## How Tool Calling Works (like Claude/Cursor)

1. User sends message
2. Claude API receives message + 5 tool definitions
3. Claude decides: "I should call `optimize_ads`"
4. We run `optimize_ads` → get result
5. Result sent back to Claude
6. Claude writes final answer with context
7. Everything streams to UI in real-time

## Pricing

- Basic: ₹2,000/month
- Pro: ₹4,500/month  
- Agency: ₹25,000/month
- 50 sellers = ₹1.5 Lakh/month
