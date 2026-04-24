# amazon_connector.py
import os
from dotenv import load_dotenv
from mock_data import PRODUCTS, REVIEWS, AD_CAMPAIGNS, ACCOUNT_HEALTH

load_dotenv()
USE_MOCK = os.getenv("ENVIRONMENT", "development") == "development"


class AmazonConnector:
    def get_inventory(self):
        if USE_MOCK:
            return PRODUCTS
        # TODO: from sp_api.api import Inventories
        # return Inventories().get_inventory_summary_marketplace()

    def get_reviews(self, days=7, unanswered_only=True):
        if USE_MOCK:
            reviews = REVIEWS
            if unanswered_only:
                reviews = [r for r in reviews if not r["is_replied"]]
            return [r for r in reviews if r["rating"] <= 2]
        # TODO: SP-API reviews

    def get_ad_campaigns(self):
        if USE_MOCK:
            return AD_CAMPAIGNS
        # TODO: Amazon Advertising API

    def get_account_health(self):
        if USE_MOCK:
            return ACCOUNT_HEALTH

    def pause_campaign(self, campaign_id: str):
        if USE_MOCK:
            return {"success": True, "campaign_id": campaign_id, "status": "paused"}

    def get_revenue_history(self):
        """Last 7 days revenue for chart"""
        return [
            {"date": "Apr 18", "revenue": 12400, "spend": 3200},
            {"date": "Apr 19", "revenue": 15800, "spend": 3800},
            {"date": "Apr 20", "revenue": 11200, "spend": 2900},
            {"date": "Apr 21", "revenue": 18600, "spend": 4100},
            {"date": "Apr 22", "revenue": 16200, "spend": 3600},
            {"date": "Apr 23", "revenue": 21000, "spend": 4800},
            {"date": "Apr 24", "revenue": 19400, "spend": 4300},
        ]

    def get_alert_log(self):
        from datetime import datetime
        return [
            {"id": 1, "type": "low_stock", "severity": "critical",
             "message": "ASIN B08N5WRWNW: Only 8 units left", "is_read": False,
             "created_at": datetime.now().isoformat()},
            {"id": 2, "type": "listing_suppressed", "severity": "high",
             "message": "Wireless Earbuds listing suppressed", "is_read": False,
             "created_at": datetime.now().isoformat()},
            {"id": 3, "type": "high_acos", "severity": "high",
             "message": "Earbuds Auto campaign ACOS 145% — paused", "is_read": True,
             "created_at": datetime.now().isoformat()},
        ]

    def get_dashboard_summary(self):
        products = self.get_inventory()
        ads = self.get_ad_campaigns()
        reviews = self.get_reviews()
        health = self.get_account_health()

        total_rev = sum(a["revenue"] for a in ads)
        total_spend = sum(a["spend"] for a in ads)
        acos = round(total_spend / total_rev * 100, 1) if total_rev else 0

        return {
            "total_products":      len(products),
            "total_revenue_today": round(total_rev, 2),
            "total_spend_today":   round(total_spend, 2),
            "estimated_profit":    round(total_rev - total_spend, 2),
            "overall_acos":        acos,
            "low_stock_count":     len([p for p in products if p["current_stock"] <= p["reorder_point"]]),
            "suppressed_count":    len([p for p in products if p["status"] == "suppressed"]),
            "unread_bad_reviews":  len(reviews),
            "high_acos_campaigns": len([a for a in ads if a["acos"] > 40]),
            "account_status":      health["overall_status"],
        }


amazon = AmazonConnector()
