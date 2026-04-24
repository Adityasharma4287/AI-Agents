# backend/agent/tool_definitions.py
# Tool schemas following agency-agents "concrete deliverables" pattern
# Each tool has: what it does, when to use it, what it returns

TOOL_DEFINITIONS = [
    {
        "name": "check_inventory",
        "description": (
            "Scan all Amazon products for stock levels. Detects: critical stockouts (<5 units), "
            "low stock (below reorder point), days-remaining estimates, and restocking recommendations. "
            "Triggers WhatsApp alerts for critical items. "
            "USE WHEN: seller asks about stock, inventory, units, maal, reorder, kitna bacha hai, "
            "products running out, or any stock-related question. "
            "RETURNS: per-product severity (CRITICAL/WARNING/OK), days remaining, recommended reorder qty."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "threshold_multiplier": {
                    "type": "number",
                    "description": "Sensitivity multiplier on reorder_point. 1.0=standard, 1.5=early warning. Default: 1.0",
                    "default": 1.0,
                }
            },
            "required": [],
        },
    },
    {
        "name": "optimize_ads",
        "description": (
            "Analyze all Sponsored Products and Sponsored Brand campaigns for ACOS efficiency. "
            "Automatically pauses campaigns above the ACOS threshold to stop daily money waste. "
            "Identifies high-performing campaigns to scale. Calculates exact rupee savings. "
            "USE WHEN: seller asks about ads, ACOS, campaigns, ad spend, paisa doob raha hai, "
            "wastage, advertising, PPC, optimize, or any ad-related question. "
            "RETURNS: per-campaign analysis, list of paused campaigns, total daily/monthly savings in ₹."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "acos_threshold": {
                    "type": "number",
                    "description": "ACOS % above which campaigns are paused. Default 40. Lower = more aggressive.",
                    "default": 40.0,
                }
            },
            "required": [],
        },
    },
    {
        "name": "monitor_reviews",
        "description": (
            "Fetch recent 1-3 star reviews that have not been replied to. "
            "Drafts professional, empathetic replies for each review maintaining seller brand voice. "
            "Requires seller approval before posting — agent never posts autonomously. "
            "USE WHEN: seller asks about reviews, ratings, complaints, negative feedback, "
            "customer unhappy, reply draft karo, review response, or star ratings. "
            "RETURNS: each review with full text + drafted reply, flagged as pending approval."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "days_back": {
                    "type": "integer",
                    "description": "How many days back to scan for reviews. Default 7.",
                    "default": 7,
                }
            },
            "required": [],
        },
    },
    {
        "name": "check_listings",
        "description": (
            "Scan all product listings for: suppressed status (zero revenue), buy box loss, "
            "pricing competitiveness issues. Provides specific fix steps for each problem. "
            "USE WHEN: seller asks about listings, suppressed, buy box, listing fix, "
            "product not showing, koi buy nahi kar raha, or listing health. "
            "RETURNS: per-listing severity, exact fix steps (image size, title length, price guidance)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "store_health_report",
        "description": (
            "Generate a complete daily health audit of the entire Amazon store. "
            "Covers: revenue, profit, ad spend, ACOS, inventory status, suppressed listings, "
            "unanswered reviews, account health metrics. Prioritizes actions by financial impact. "
            "USE WHEN: seller asks for full report, daily summary, aaj ka status, "
            "overall kaise chal raha hai, sab kuch batao, health check, or general store status. "
            "RETURNS: complete store scorecard with priority action list ranked by ₹ impact."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
]
