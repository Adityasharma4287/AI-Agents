# backend/agent/tool_executor.py
# When Claude decides to call a tool, this file runs the actual logic

from datetime import datetime
from amazon_connector import amazon
from notifications import notify


def run_tool(tool_name: str, tool_input: dict) -> str:
    """Route tool call to the right function"""
    handlers = {
        "check_inventory":    _check_inventory,
        "optimize_ads":       _optimize_ads,
        "monitor_reviews":    _monitor_reviews,
        "check_listings":     _check_listings,
        "store_health_report":_store_health_report,
    }
    handler = handlers.get(tool_name)
    if not handler:
        return f"Unknown tool: {tool_name}"
    return handler(tool_input)


# ─────────────────────────────────────────────────────────────
# TOOL 1: INVENTORY
# ─────────────────────────────────────────────────────────────
def _check_inventory(inp: dict) -> str:
    mult = inp.get("threshold_multiplier", 1.0)
    products = amazon.get_inventory()
    issues = []

    for p in products:
        stock, reorder = p["current_stock"], p["reorder_point"]
        if stock <= reorder * mult:
            severity = "CRITICAL" if stock <= 5 else "WARNING"
            days_left = max(1, stock // max(1, p["monthly_sales"] // 30))
            recommended = reorder * 3
            issues.append({
                "asin": p["asin"],
                "title": p["title"],
                "stock": stock,
                "reorder": reorder,
                "days_left": days_left,
                "recommended_reorder": recommended,
                "severity": severity,
            })
            msg = (
                f"{'🚨 CRITICAL' if severity=='CRITICAL' else '⚠️ WARNING'}: Low Stock!\n"
                f"Product: {p['title']}\nASIN: {p['asin']}\n"
                f"Stock: {stock} units | Reorder Point: {reorder}\n"
                f"Days Remaining: ~{days_left} days\n"
                f"Recommended Reorder: {recommended} units"
            )
            notify(msg)

    if not issues:
        return "✅ All products have healthy stock. No action needed."

    lines = [f"Found {len(issues)} low-stock products:\n"]
    for i in issues:
        lines.append(
            f"[{i['severity']}] {i['title']}\n"
            f"  ASIN: {i['asin']}\n"
            f"  Stock: {i['stock']} units | Reorder at: {i['reorder']}\n"
            f"  Days remaining: ~{i['days_left']} days\n"
            f"  → Reorder {i['recommended_reorder']} units NOW\n"
        )
    lines.append(f"WhatsApp alerts sent for {len(issues)} products.")
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────
# TOOL 2: ADS
# ─────────────────────────────────────────────────────────────
def _optimize_ads(inp: dict) -> str:
    threshold = inp.get("acos_threshold", 40.0)
    campaigns = amazon.get_ad_campaigns()
    paused, good, total_saved = [], [], 0

    for c in campaigns:
        if c["acos"] > threshold and c["status"] == "active":
            amazon.pause_campaign(c["campaign_id"])
            total_saved += c["spend"]
            paused.append(c)
            notify(
                f"⏸️ Campaign Paused by AI Agent\n"
                f"Campaign: {c['campaign_name']}\nACOS: {c['acos']}%\n"
                f"Daily spend saved: ₹{c['spend']:,.0f}\n"
                f"Reason: ACOS > {threshold}% threshold"
            )
        elif c["acos"] < 25 and c["acos"] > 0:
            good.append(c)

    if not paused and not good:
        return f"All campaigns within acceptable ACOS range (<{threshold}%). No action needed."

    lines = []
    if paused:
        lines.append(f"⏸️ Paused {len(paused)} high-ACOS campaigns:\n")
        for c in paused:
            lines.append(
                f"  • {c['campaign_name']}\n"
                f"    ACOS: {c['acos']}% | Daily spend saved: ₹{c['spend']:,.0f}\n"
            )
        lines.append(f"💰 Total daily savings: ₹{total_saved:,.0f}")
        lines.append(f"📅 Monthly savings if continued: ₹{total_saved*30:,.0f}\n")
    if good:
        lines.append(f"✅ {len(good)} campaigns performing well (consider scaling budget):")
        for c in good:
            lines.append(f"  • {c['campaign_name']} — ACOS {c['acos']}%")
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────
# TOOL 3: REVIEWS
# ─────────────────────────────────────────────────────────────
def _monitor_reviews(inp: dict) -> str:
    days = inp.get("days_back", 7)
    reviews = amazon.get_reviews(days=days, unanswered_only=True)

    if not reviews:
        return f"✅ No unanswered negative reviews in the last {days} days."

    lines = [f"Found {len(reviews)} negative reviews needing replies:\n"]
    for r in reviews:
        reply = _draft_reply(r)
        lines.append(
            f"{'★' * r['rating']}{'☆' * (5 - r['rating'])} by {r['reviewer_name']} "
            f"({'Verified' if r['verified_purchase'] else 'Unverified'})\n"
            f"Title: \"{r['title']}\"\n"
            f"Review: \"{r['body'][:120]}...\"\n"
            f"\nDraft Reply:\n{reply}\n"
            f"{'─'*50}\n"
        )
        notify(
            f"⭐ {r['rating']}/5 Negative Review!\n"
            f"{r['reviewer_name']}: {r['title']}\n"
            f"Draft reply prepared — please review & approve."
        )
    lines.append("⚠️ Replies need seller approval before posting on Amazon.")
    return "\n".join(lines)


def _draft_reply(review: dict) -> str:
    name = review["reviewer_name"].split()[0]
    if review["rating"] == 1:
        return (
            f"Dear {name},\n\n"
            "Thank you for your feedback. We sincerely apologize that our product did not meet "
            "your expectations. This is not the quality standard we strive for.\n\n"
            "Please contact us directly and we will arrange a full replacement or complete refund, "
            "whichever you prefer — no questions asked.\n\n"
            "We take every review seriously and will use this to improve our product.\n\n"
            "Warm regards,\nCustomer Care Team"
        )
    return (
        f"Dear {name},\n\n"
        "Thank you for sharing your experience with us. We're genuinely sorry to hear about "
        "the issue you faced with our product.\n\n"
        "Please reach out to us directly and we will make sure this is resolved for you with "
        "either a replacement or full refund at your convenience.\n\n"
        "Best regards,\nCustomer Care Team"
    )


# ─────────────────────────────────────────────────────────────
# TOOL 4: LISTINGS
# ─────────────────────────────────────────────────────────────
def _check_listings(inp: dict) -> str:
    products = amazon.get_inventory()
    issues = []

    for p in products:
        product_issues = []
        fixes = []

        if p["status"] == "suppressed":
            product_issues.append("❌ Listing is SUPPRESSED by Amazon")
            fixes += [
                "Check main image: must be 1000×1000px minimum on white background",
                "Verify title is under 200 characters",
                "Go to: Seller Central → Inventory → Fix Stranded Inventory",
                "Ensure all required attributes are filled (brand, size, colour)",
            ]

        if p["buy_box_percentage"] == 0:
            product_issues.append("🏆 Buy Box completely LOST")
            fixes += [
                "Check if you're eligible for Buy Box (FBA preferred)",
                "Match or beat lowest competitor price by 2-3%",
                "Check seller feedback score (must be >4.0)",
            ]
        elif p["buy_box_percentage"] < 60:
            product_issues.append(f"⚠️ Buy Box low: {p['buy_box_percentage']}% (target >80%)")
            fixes.append("Competitive repricing may help win more Buy Box share")

        if product_issues:
            issues.append({
                "asin": p["asin"],
                "title": p["title"],
                "issues": product_issues,
                "fixes": fixes[:4],
            })
            notify(f"⚠️ Listing Issue: {p['title']}\n" + "\n".join(product_issues))

    if not issues:
        return "✅ All listings are healthy. No suppressed listings found."

    lines = [f"Found issues in {len(issues)} listing(s):\n"]
    for item in issues:
        lines.append(f"📦 {item['title']}\n   ASIN: {item['asin']}")
        for issue in item["issues"]:
            lines.append(f"   {issue}")
        lines.append("   Recommended Fixes:")
        for fix in item["fixes"]:
            lines.append(f"   → {fix}")
        lines.append("")
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────
# TOOL 5: HEALTH REPORT
# ─────────────────────────────────────────────────────────────
def _store_health_report(inp: dict) -> str:
    s = amazon.get_dashboard_summary()
    h = amazon.get_account_health()
    ts = datetime.now().strftime("%d %b %Y, %I:%M %p")

    return (
        f"📊 SELLERPILOT DAILY REPORT\n"
        f"Generated: {ts}\n"
        f"{'═'*44}\n\n"
        f"💰 TODAY'S PERFORMANCE\n"
        f"   Revenue:          ₹{s['total_revenue_today']:>10,.0f}\n"
        f"   Ad Spend:         ₹{s['total_spend_today']:>10,.0f}\n"
        f"   Estimated Profit: ₹{s['estimated_profit']:>10,.0f}\n"
        f"   Overall ACOS:     {s['overall_acos']}%\n\n"
        f"📦 INVENTORY\n"
        f"   Total Products:      {s['total_products']}\n"
        f"   Low Stock Items:     {s['low_stock_count']} {'⚠️ ACTION NEEDED' if s['low_stock_count'] else '✅'}\n"
        f"   Suppressed Listings: {s['suppressed_count']} {'❌ URGENT' if s['suppressed_count'] else '✅'}\n\n"
        f"⭐ REVIEWS\n"
        f"   Negative (unread):   {s['unread_bad_reviews']} {'⚠️' if s['unread_bad_reviews'] else '✅'}\n\n"
        f"📢 ADVERTISING\n"
        f"   High ACOS Campaigns: {s['high_acos_campaigns']} {'💸 WASTING MONEY' if s['high_acos_campaigns'] else '✅'}\n\n"
        f"🏥 ACCOUNT HEALTH\n"
        f"   Order Defect Rate:   {h['order_defect_rate']}% {'✅' if h['order_defect_rate'] < 1 else '⚠️'}\n"
        f"   Late Shipment Rate:  {h['late_shipment_rate']}% {'✅' if h['late_shipment_rate'] < 4 else '⚠️'}\n"
        f"   Valid Tracking:      {h['valid_tracking_rate']}%\n"
        f"   Overall Status:      {h['overall_status']}\n\n"
        f"{'═'*44}\n"
        f"🚨 TOTAL ALERTS: {s['low_stock_count'] + s['suppressed_count'] + s['unread_bad_reviews'] + s['high_acos_campaigns']}"
    )
