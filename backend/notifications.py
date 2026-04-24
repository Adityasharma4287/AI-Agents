# backend/utils/notifications.py
import os
from dotenv import load_dotenv
load_dotenv()

IS_DEV = os.getenv("ENVIRONMENT", "development") == "development"


def notify(message: str):
    """Send WhatsApp alert. In dev mode just prints."""
    if IS_DEV:
        print(f"\n📱 [ALERT]\n{message}\n{'─'*40}")
        return
    try:
        from twilio.rest import Client
        client = Client(os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"))
        client.messages.create(
            body=message,
            from_=os.getenv("TWILIO_WHATSAPP_FROM"),
            to=os.getenv("SELLER_WHATSAPP"),
        )
    except Exception as e:
        print(f"[notify error] {e}")
