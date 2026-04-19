# backend/tools/agent_tools.py
# ============================================================
# YEH FILE: Agent ke "haath" hain - woh kya kya kar sakta hai
# Har tool ek kaam karta hai
# Agent decide karta hai kaunsa tool kab use karna hai
# ============================================================

from langchain.tools import tool
from tools.amazon_connector import amazon
from utils.notifications import send_whatsapp_alert, send_email_alert
from datetime import datetime


# ============================================================
# TOOL 1: INVENTORY CHECK & RESTOCK ALERT
# ============================================================
@tool
def check_inventory_and_alert(threshold_multiplier: float = 1.0) -> str:
    """
    Inventory check karo aur low stock products ke liye alert bhejo.
    Jab kisi product ka stock reorder_point se kam ho tab yeh tool use karo.
    Returns: List of low stock products with recommended reorder quantities.
    """
    products = amazon.get_inventory()
    low_stock_products = []
    alerts_sent = []

    for product in products:
        stock = product["current_stock"]
        reorder = product["reorder_point"]

        if stock <= reorder * threshold_multiplier:
            severity = "CRITICAL" if stock <= 5 else "WARNING"
            days_remaining = max(1, stock // 3)  # Assume 3 units/day sales velocity

            alert_msg = f"""
🚨 {severity}: Low Stock Alert
Product: {product['title']}
ASIN: {product['asin']}
Current Stock: {stock} units
Reorder Point: {reorder} units
Estimated Days Remaining: {days_remaining} days
Recommended Reorder: {reorder * 3} units

ACTION NEEDED: Place reorder immediately to avoid stockout!
            """.strip()

            low_stock_products.append({
                "asin": product["asin"],
                "title": product["title"],
                "stock": stock,
                "days_remaining": days_remaining,
                "recommended_reorder": reorder * 3,
                "severity": severity
            })

            # WhatsApp/Email alert bhejo
            send_whatsapp_alert(alert_msg)
            alerts_sent.append(product["asin"])

    if not low_stock_products:
        return "✅ All products have healthy stock levels. No action needed."

    result = f"⚠️ Found {len(low_stock_products)} low stock products:\n\n"
    for p in low_stock_products:
        result += f"• [{p['severity']}] {p['title']}\n"
        result += f"  Stock: {p['stock']} units | Reorder {p['recommended_reorder']} units\n"
        result += f"  Approx {p['days_remaining']} days remaining\n\n"

    result += f"\n📱 Alerts sent to seller for {len(alerts_sent)} products."
    return result


# ============================================================
# TOOL 2: LISTING HEALTH CHECK
# ============================================================
@tool
def check_and_fix_listings() -> str:
    """
    Suppressed ya unhealthy listings check karo.
    Jab listings mein issues ho (suppressed, buy box lost) tab use karo.
    Returns: List of listing issues with recommended fixes.
    """
    products = amazon.get_inventory()
    issues_found = []

    for product in products:
        issues = []

        if product["status"] == "suppressed":
            issues.append("❌ Listing is SUPPRESSED - Amazon ne hide kar diya")

        if product["buy_box_percentage"] == 0:
            issues.append("🏆 Buy Box LOST - Koi competitor le gaya")
        elif product["buy_box_percentage"] < 50:
            issues.append(f"⚠️ Buy Box low: {product['buy_box_percentage']}% (should be >70%)")

        if product["price"] > 2000 and product["buy_box_percentage"] < 60:
            issues.append("💰 Price might be too high compared to competitors")

        if issues:
            fix_suggestions = generate_listing_fixes(product, issues)
            issues_found.append({
                "asin": product["asin"],
                "title": product["title"],
                "issues": issues,
                "fixes": fix_suggestions
            })

            alert_msg = f"⚠️ Listing Issue Detected!\n{product['title']}\n" + "\n".join(issues)
            send_whatsapp_alert(alert_msg)

    if not issues_found:
        return "✅ All listings are healthy. No suppressed listings found."

    result = f"🔍 Found issues in {len(issues_found)} listings:\n\n"
    for item in issues_found:
        result += f"📦 {item['title']} (ASIN: {item['asin']})\n"
        for issue in item["issues"]:
            result += f"  {issue}\n"
        result += f"  💡 Recommended Fixes:\n"
        for fix in item["fixes"]:
            result += f"    → {fix}\n"
        result += "\n"

    return result


def generate_listing_fixes(product: dict, issues: list) -> list:
    """Issues ke hisaab se fixes suggest karo"""
    fixes = []
    for issue in issues:
        if "SUPPRESSED" in issue:
            fixes.extend([
                "Check images - minimum 1000x1000 pixels required",
                "Verify title length is under 200 characters",
                "Ensure all required attributes are filled",
                "Go to: Seller Central > Inventory > Fix Stranded Inventory"
            ])
        if "Buy Box" in issue:
            fixes.extend([
                "Check competitor prices and match or beat by 2-5%",
                "Ensure seller feedback rating is above 4.5",
                "Verify you have Prime eligibility (FBA preferred)"
            ])
    return fixes[:4]  # Max 4 fixes


# ============================================================
# TOOL 3: REVIEW MONITORING & AI REPLY DRAFTING
# ============================================================
@tool
def monitor_reviews_and_draft_replies() -> str:
    """
    Negative reviews check karo aur AI se professional reply draft karo.
    Jab 1-2 star reviews aaye tab yeh tool use karo.
    Returns: Drafted replies for each negative review that needs attention.
    """
    reviews = amazon.get_reviews()
    negative_reviews = [r for r in reviews if r["rating"] <= 2 and not r["is_replied"]]

    if not negative_reviews:
        return "✅ No new negative reviews found. All reviews are handled."

    drafted_replies = []

    for review in negative_reviews:
        reply = draft_ai_reply(review)
        drafted_replies.append({
            "review_id": review["review_id"],
            "asin": review["asin"],
            "rating": review["rating"],
            "customer": review["reviewer_name"],
            "review_title": review["title"],
            "draft_reply": reply
        })

        alert_msg = f"⭐ {review['rating']}/5 Negative Review!\n{review['reviewer_name']}: {review['title']}\nDraft reply prepared. Please review and post."
        send_whatsapp_alert(alert_msg)

    result = f"📝 {len(drafted_replies)} negative reviews found. Draft replies prepared:\n\n"
    for dr in drafted_replies:
        result += f"Review by {dr['customer']} ({dr['rating']}⭐): {dr['review_title']}\n"
        result += f"Draft Reply:\n{dr['draft_reply']}\n"
        result += "─" * 50 + "\n\n"

    result += "⚠️ NOTE: Please review and approve these replies before posting. Agent cannot post without seller approval."
    return result


def draft_ai_reply(review: dict) -> str:
    """Review ke liye professional reply draft karo"""
    # Simple template-based replies (GPT se aur better milega production mein)
    if review["rating"] == 1:
        return f"""Dear {review['reviewer_name']},

Thank you for your feedback. We sincerely apologize for your experience with our product. This is not the quality standard we aim to provide.

We would like to make this right for you. Please contact us at seller-support@ourstore.com and we will arrange either a full replacement or a complete refund - whichever you prefer.

We take quality seriously and your feedback helps us improve. We hope to have the opportunity to restore your trust.

Warm regards,
Customer Care Team"""
    else:
        return f"""Dear {review['reviewer_name']},

Thank you for sharing your experience. We're sorry to hear about the issue you faced. 

Please reach out to us directly and we'll resolve this for you with a replacement or refund. Your satisfaction is our priority.

Best regards,
Customer Care Team"""


# ============================================================
# TOOL 4: AD CAMPAIGN OPTIMIZATION
# ============================================================
@tool
def optimize_ad_campaigns(acos_threshold: float = 40.0) -> str:
    """
    Ad campaigns analyze karo aur high ACOS campaigns pause karo.
    ACOS (Advertising Cost of Sale) agar threshold se zyada ho to campaign waste kar raha hai.
    Default threshold: 40% (matlab ₹100 revenue ke liye ₹40 se zyada ad spend = loss)
    Returns: List of actions taken on campaigns.
    """
    campaigns = amazon.get_ad_performance()
    actions_taken = []
    total_saved = 0

    for campaign in campaigns:
        acos = campaign["acos"]
        daily_spend = campaign["spend"]

        if acos > acos_threshold and campaign["status"] == "active":
            # Campaign pause karo
            result = amazon.pause_campaign(campaign["campaign_id"])

            projected_daily_savings = daily_spend
            total_saved += projected_daily_savings

            action = {
                "campaign": campaign["campaign_name"],
                "action": "PAUSED",
                "acos_was": acos,
                "daily_spend": daily_spend,
                "reason": f"ACOS {acos}% is above threshold {acos_threshold}%",
                "daily_savings": projected_daily_savings
            }
            actions_taken.append(action)

            alert_msg = f"""⏸️ Campaign Paused by AI Agent
Campaign: {campaign['campaign_name']}
ACOS: {acos}% (too high!)
Daily Spend Saved: ₹{daily_spend:,.0f}

Reason: ACOS exceeds {acos_threshold}% threshold. Paused to prevent losses.
You can review and re-enable from dashboard."""
            send_whatsapp_alert(alert_msg)

        elif acos < 20 and acos > 0:
            # Good campaign - suggest increasing budget
            actions_taken.append({
                "campaign": campaign["campaign_name"],
                "action": "SUGGESTION",
                "acos_was": acos,
                "reason": f"ACOS {acos}% is excellent. Consider increasing budget by 20-30%.",
                "daily_savings": 0
            })

    if not actions_taken:
        return f"✅ All campaigns are within acceptable ACOS range (below {acos_threshold}%). No action needed."

    result = f"📊 Ad Campaign Optimization Complete:\n\n"
    paused = [a for a in actions_taken if a["action"] == "PAUSED"]
    suggestions = [a for a in actions_taken if a["action"] == "SUGGESTION"]

    if paused:
        result += f"⏸️ PAUSED {len(paused)} campaigns:\n"
        for a in paused:
            result += f"  • {a['campaign']}\n"
            result += f"    ACOS: {a['acos_was']}% | Daily savings: ₹{a['daily_spend']:,.0f}\n"
        result += f"\n💰 Total daily ad spend saved: ₹{total_saved:,.0f}\n\n"

    if suggestions:
        result += f"💡 {len(suggestions)} campaigns performing well (consider scaling):\n"
        for a in suggestions:
            result += f"  • {a['campaign']} - ACOS: {a['acos_was']}%\n"

    return result


# ============================================================
# TOOL 5: FULL STORE HEALTH REPORT
# ============================================================
@tool
def generate_store_health_report() -> str:
    """
    Complete store health report banao - ek baar mein sab check karo.
    Subah ka daily report ya kisi bhi time complete status ke liye use karo.
    Returns: Comprehensive health report of the Amazon store.
    """
    summary = amazon.get_dashboard_summary()
    account_health = amazon.get_account_health()
    timestamp = datetime.now().strftime("%d %b %Y, %I:%M %p")

    report = f"""
📊 SELLERPILOT DAILY REPORT
Generated: {timestamp}
{'='*45}

💰 TODAY'S PERFORMANCE
  Revenue:        ₹{summary['total_revenue_today']:,.0f}
  Ad Spend:       ₹{summary['total_ad_spend_today']:,.0f}
  Overall ACOS:   {summary['overall_acos']}%
  Net Est. Profit: ₹{summary['total_revenue_today'] - summary['total_ad_spend_today']:,.0f}

📦 INVENTORY STATUS
  Total Products:       {summary['total_products']}
  Low Stock Items:      {summary['low_stock_count']} {'⚠️ ACTION NEEDED' if summary['low_stock_count'] > 0 else '✅'}
  Suppressed Listings:  {summary['suppressed_listings']} {'❌ URGENT' if summary['suppressed_listings'] > 0 else '✅'}

⭐ CUSTOMER FEEDBACK  
  Negative Reviews (unread): {summary['unread_bad_reviews']} {'⚠️' if summary['unread_bad_reviews'] > 0 else '✅'}

📢 ADVERTISING
  High ACOS Campaigns: {summary['high_acos_campaigns']} {'💸 WASTING MONEY' if summary['high_acos_campaigns'] > 0 else '✅'}

🏥 ACCOUNT HEALTH
  Order Defect Rate:    {account_health['order_defect_rate']}% {'⚠️' if account_health['order_defect_rate'] > 1 else '✅'}
  Late Shipment Rate:   {account_health['late_shipment_rate']}% {'⚠️' if account_health['late_shipment_rate'] > 4 else '✅'}
  Overall Status:       {account_health['overall_status']}

🚨 TOTAL ALERTS: {summary['alerts_count']}
{'='*45}
    """.strip()

    return report


# ============================================================
# ALL TOOLS LIST - Agent ko yahi denge
# ============================================================
ALL_TOOLS = [
    check_inventory_and_alert,
    check_and_fix_listings,
    monitor_reviews_and_draft_replies,
    optimize_ad_campaigns,
    generate_store_health_report,
]
