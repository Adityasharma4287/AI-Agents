# SellerPilot AI 🤖

**Autonomous AI Agent for Indian Amazon Sellers — Powered by Anthropic Claude**

---

## ⚡ Quick Start

### 1. Clone & Setup
```bash
git clone https://github.com/YOUR_USERNAME/AI-Agents.git
cd AI-Agents
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
👉 Key yahan milegi: **console.anthropic.com**

### 3. Run
```bash
python main.py
```
Browser mein kholo: **http://localhost:8000/docs**

---

## 📁 Project Structure

```
AI-Agents/
├── main.py              # FastAPI server — entry point
├── core.py              # AI Agent (Claude powered)
├── amazon_connector.py  # Amazon data connector
├── mock_data.py         # Test data (dev mode)
├── tool_definitions.py  # Agent tools schema
├── tool_executor.py     # Tool logic
├── notifications.py     # WhatsApp alerts (Twilio)
├── config.js            # Frontend config
├── index.html           # Main dashboard UI
├── sellerpilot_agent.html # Chat UI
├── requirements.txt     # Python packages
├── .env.example         # Environment template
└── .gitignore           # Secret files blocked
```

---

## 🛠️ Features

- 📦 **Inventory Monitor** — Low stock alerts with days remaining
- 📢 **Ad Optimizer** — Auto-pause high ACOS campaigns, save ₹₹₹
- ⭐ **Review Manager** — Draft replies for negative reviews
- 🏷️ **Listing Health** — Detect suppressed listings instantly
- 📊 **Daily Report** — Full store audit with rupee impact

---

## 🔑 Environment Variables

| Variable | Description |
|----------|-------------|
| `ANTHROPIC_API_KEY` | Claude API key (console.anthropic.com) |
| `ENVIRONMENT` | `development` = mock data, `production` = real Amazon |
| `TWILIO_ACCOUNT_SID` | WhatsApp alerts (optional) |
| `TWILIO_AUTH_TOKEN` | WhatsApp alerts (optional) |
| `SELLER_WHATSAPP` | Your WhatsApp number (optional) |

---

## ⚠️ Important

**Never push `.env` to GitHub** — it contains your API keys.
`.gitignore` already blocks it. Keep your keys safe!
