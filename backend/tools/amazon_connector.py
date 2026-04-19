
class AmazonConnector:
    def get_dashboard_summary(self):
        return {
            'total_revenue_today': 15000,
            'total_ad_spend_today': 2500,
            'overall_acos': 18.5,
            'total_products': 50,
            'low_stock_count': 2,
            'suppressed_listings': 0,
            'unread_bad_reviews': 1,
            'high_acos_campaigns': 1,
            'alerts_count': 4
        }
    def get_account_health(self):
        return {
            'order_defect_rate': 0.5,
            'late_shipment_rate': 1.2,
            'overall_status': 'Healthy'
        }
    def get_inventory(self):
        return [
            {'asin': 'B08N5WRWNW', 'title': 'Product A', 'current_stock': 8, 'reorder_point': 20, 'status': 'active', 'buy_box_percentage': 95, 'price': 1500},
            {'asin': 'B07XQXZABC', 'title': 'Product B', 'current_stock': 50, 'reorder_point': 10, 'status': 'suppressed', 'buy_box_percentage': 0, 'price': 2500}
        ]
    def get_reviews(self):
        return [
            {'review_id': '1', 'asin': 'B08N5WRWNW', 'rating': 2, 'reviewer_name': 'John', 'title': 'Bad quality', 'is_replied': False}
        ]
    def get_ad_performance(self):
        return [
            {'campaign_id': 'c1', 'campaign_name': 'Earbuds - Auto', 'acos': 45.0, 'spend': 500, 'status': 'active'}
        ]
    def pause_campaign(self, campaign_id):
        return True

amazon = AmazonConnector()
