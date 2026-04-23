# backend/tools/amazon_connector.py
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

    def get_dashboard_summary(self):
        products  = self.get_inventory()
        ads       = self.get_ad_campaigns()
        reviews   = self.get_reviews()
        health    = self.get_account_health()

        total_rev   = sum(a["revenue"] for a in ads)
        total_spend = sum(a["spend"]   for a in ads)
        acos        = round(total_spend / total_rev * 100, 1) if total_rev else 0

        return {
            "total_products":       len(products),
            "total_revenue_today":  round(total_rev, 2),
            "total_spend_today":    round(total_spend, 2),
            "estimated_profit":     round(total_rev - total_spend, 2),
            "overall_acos":         acos,
            "low_stock_count":      len([p for p in products if p["current_stock"] <= p["reorder_point"]]),
            "suppressed_count":     len([p for p in products if p["status"] == "suppressed"]),
            "unread_bad_reviews":   len(reviews),
            "high_acos_campaigns":  len([a for a in ads if a["acos"] > 40]),
            "account_status":       health["overall_status"],
        }


amazon = AmazonConnector()
