# 🤖 SellerPilot AI — Amazon Seller Agent

> **AI Agent jo Amazon store 24/7 khud dekh-bhal karta hai**

---

## 🎯 Yeh kya karta hai?

| Feature | Kya hota hai |
|---------|-------------|
| 📦 Inventory Monitor | Stock kam ho to alert + WhatsApp message |
| ❌ Listing Fix | Suppressed listings detect karta hai |
| ⭐ Review Handler | Negative reviews ke liye AI reply draft karta hai |
| 💸 Ad Optimizer | High ACOS campaigns automatically pause karta hai |
| 📊 Daily Report | Subah 9 baje complete health report bhejta hai |

---

## 📁 Project Structure

```
sellerpilot/
├── backend/
│   ├── main.py                  ← Server (FastAPI)
│   ├── requirements.txt         ← Python packages
│   ├── .env.example             ← API keys template
│   ├── agent/
│   │   └── sellerpilot_agent.py ← 🧠 Agent ka dimaag
│   ├── tools/
│   │   ├── amazon_connector.py  ← Amazon se data fetch
│   │   └── agent_tools.py       ← Agent ke haath (tools)
│   ├── models/
│   │   └── database.py          ← Database tables
│   └── utils/
│       └── notifications.py     ← WhatsApp / Email alerts
└── frontend/
    └── dashboard.html           ← 🖥️ Seller Dashboard
```

---

## 🚀 Quick Start (5 Minutes)

### Step 1: Clone / Download karo
```bash
cd sellerpilot
```

### Step 2: Setup run karo
```bash
chmod +x setup.sh
./setup.sh
```

### Step 3: Server start karo
```bash
cd backend
source venv/bin/activate      # Mac/Linux
# venv\Scripts\activate       # Windows
python3 -m uvicorn main:app --reload
```

### Step 4: Dashboard open karo
```
frontend/dashboard.html   ← browser mein open karo (double click)
```

### Step 5: API test karo
```
http://localhost:8000/docs   ← Swagger UI mein sab test karo
```

---

## 🔑 API Keys Kahan Se Milenge?

### OpenAI API Key (Agent ke liye)
1. https://platform.openai.com/api-keys jaao
2. "Create new secret key" karo
3. `sk-...` copy karo
4. `backend/.env` mein `OPENAI_API_KEY=sk-...` paste karo

> **Bina OpenAI key ke bhi chal sakta hai** — Mock mode mein sab tools directly test kar sakte ho

### Amazon SP-API (Real data ke liye)
1. https://sellercentral.amazon.in/apps/manage
2. Developer Console > Add App
3. Client ID, Client Secret, Refresh Token milega
4. `.env` mein paste karo

> **Pehle mock data se test karo, phir real keys add karo**

---

## 💡 Agent ko kaise use karein?

### Dashboard se (Frontend):
1. `frontend/dashboard.html` browser mein open karo
2. Left sidebar se tab choose karo
3. "Run Full Check" button dabao

### API se (Backend):
```bash
# Agent ko task do
curl -X POST http://localhost:8000/agent/run \
  -H "Content-Type: application/json" \
  -d '{"task": "Check inventory and alert for low stock"}'

# Daily routine trigger karo
curl -X POST http://localhost:8000/agent/daily-routine

# Dashboard summary
curl http://localhost:8000/dashboard
```

---

## 📱 WhatsApp Alerts Setup (Optional)

1. https://www.twilio.com/try-twilio jaao (free account)
2. WhatsApp Sandbox enable karo
3. Twilio keys `.env` mein daalo:
```
TWILIO_ACCOUNT_SID=ACxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxx
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
SELLER_WHATSAPP_NUMBER=whatsapp:+91XXXXXXXXXX
```

---

## 💰 Isse Sell Kaise Karein?

### Pricing Model:
```
Basic Plan:   ₹2,000/month  → Monitoring + Alerts
Pro Plan:     ₹4,500/month  → Auto-actions + Dashboard
Agency Plan:  ₹25,000/month → Unlimited seller accounts
```

### 50 Sellers = ₹1.5 Lakh/month recurring!

### Marketing Channels:
1. **YouTube Demo** — "Mera AI agent ne ₹4,050 ka daily ad waste band kiya"
2. **Amazon Seller FB Groups** — Free trial do, testimonials lo
3. **Agencies** — White-label deal, unke clients aapke agent pe
4. **LinkedIn** — Amazon success stories post karo

---

## 🔧 Customization

### Apna threshold change karna ho to:
```python
# backend/tools/agent_tools.py
optimize_ad_campaigns(acos_threshold=35.0)  # 35% karo
check_inventory_and_alert(threshold_multiplier=1.5)  # 50% zyada buffer
```

### Schedule change karna ho to:
```python
# backend/main.py
scheduler.add_job(run_scheduled_check, "interval", hours=2)  # Har 2 ghante
scheduler.add_job(run_daily_morning_routine, "cron", hour=8, minute=30)  # 8:30 AM
```

---

## 🐛 Common Issues

| Problem | Solution |
|---------|----------|
| `ModuleNotFoundError` | `pip install -r requirements.txt` again run karo |
| `OPENAI_API_KEY not set` | Mock mode mein chal raha hai — OK hai |
| CORS error | Backend chal raha hai? `http://localhost:8000/health` check karo |
| No alerts showing | Mock data use ho raha hai — expected behavior |

---

## 📞 Support

Koi issue ho to:
- Check karo `backend/.env` mein sab keys sahi hain
- `python3 -m uvicorn main:app --reload` se server restart karo
- `http://localhost:8000/docs` mein API test karo

---

**Built with:** FastAPI · LangChain · GPT-4o-mini · Amazon SP-API · SQLite/PostgreSQL
