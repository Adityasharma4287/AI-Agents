# backend/agent/tool_definitions.py
# These are passed to Claude API as tools= parameter
# Claude decides WHICH tool to call and WHEN

TOOL_DEFINITIONS = [
    {
        "name": "check_inventory",
        "description": (
            "Check inventory levels for all Amazon products. "
            "Detects low stock, critical stock, and stockouts. "
            "Use this when seller asks about stock, inventory, units, maal, products running out, "
            "reorder, ya koi product kitna bacha hai."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "threshold_multiplier": {
                    "type": "number",
                    "description": "Multiply reorder_point by this. Default 1.0. Use 1.5 for early warning.",
                    "default": 1.0,
                }
            },
            "required": [],
        },
    },
    {
        "name": "optimize_ads",
        "description": (
            "Analyze all Amazon ad campaigns. Identifies campaigns with high ACOS (wasteful). "
            "Pauses campaigns above the threshold automatically. "
            "Use this when seller asks about ads, ACOS, campaigns, ad spend, wastage, paisa doob raha hai, "
            "advertising performance."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "acos_threshold": {
                    "type": "number",
                    "description": "ACOS % above which campaigns are paused. Default 40.",
                    "default": 40.0,
                }
            },
            "required": [],
        },
    },
    {
        "name": "monitor_reviews",
        "description": (
            "Fetch recent negative reviews (1-2 star) and draft professional reply for each. "
            "Use this when seller asks about reviews, ratings, complaints, customer feedback, "
            "negative comments, reply draft karo."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "days_back": {
                    "type": "integer",
                    "description": "How many days back to look for reviews. Default 7.",
                    "default": 7,
                }
            },
            "required": [],
        },
    },
    {
        "name": "check_listings",
        "description": (
            "Check health of all Amazon product listings. Detects suppressed listings, "
            "low buy box percentage, pricing issues. Gives fix suggestions. "
            "Use this for listing health, suppressed, buy box, listing fix."
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
            "Generate a complete daily health report of the Amazon store. "
            "Covers inventory, ads, reviews, listings, account health — everything. "
            "Use this for 'full report', 'aaj ka status', 'overall kaise chal raha hai', "
            "'daily report', 'store health'."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
]
