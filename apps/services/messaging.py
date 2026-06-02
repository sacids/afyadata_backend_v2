import logging
import random
import re
import requests

from django.conf import settings

logger = logging.getLogger(__name__)


class MessagingService:
    TOKEN_BASE_URL = "https://api.orange.com/oauth/v3/token"
    SMS_BASE_URL = (
        "https://api.orange.com/smsmessaging/v1/"
        "outbound/tel%3A%2B224622731178/requests"
    )

    SENDER_ADDRESS = "tel:+224622731178"
    COUNTRY_CODE = "+224"

    def __init__(self):
        self.orange_token = settings.ORANGE_TOKEN

    def create_token(self):
        """Create access token using Orange API"""
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {self.orange_token}",
        }

        response = requests.post(
            self.TOKEN_BASE_URL,
            headers=headers,
            data={"grant_type": "client_credentials"},
            timeout=30,
        )

        response.raise_for_status()

        data = response.json()
        return data.get("access_token")


    def send_sms(self, phone, message):
        """Send SMS using Orange API"""
        api_token = self.create_token()

        phone = self.cast_mobile(phone)

        payload = {
            "outboundSMSMessageRequest": {
                "address": f"tel:{phone}",
                "senderAddress": self.SENDER_ADDRESS,
                "outboundSMSTextMessage": {
                    "message": message
                },
            }
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_token}",
        }

        response = requests.post(
            self.SMS_BASE_URL,
            json=payload,
            headers=headers,
            timeout=30,
        )

        logger.debug("Orange SMS response: %s", response.text)

        response.raise_for_status()

        return {
            "error": False,
            "success_msg": "Message sent",
            "response": response.json() if response.text else None,
        }

    def generate_message_id(self):
        characters = "123456789ABCDEFGHJKLMNPQRSTUVWXYZ"
        return "".join(random.choice(characters) for _ in range(11))

    def cast_mobile(self, mobile):
        mobile = str(mobile).strip().replace(" ", "")

        if re.match(r"^0\d+$", mobile):
            return f"{self.COUNTRY_CODE}{mobile[1:]}"

        if mobile.startswith("+224"):
            return mobile

        if mobile.startswith("224"):
            return f"+{mobile}"

        if len(mobile) == 9:
            return f"{self.COUNTRY_CODE}{mobile}"

        return mobile

    def trim_zero_mobile(self, mobile):
        mobile = str(mobile).strip().replace(" ", "")

        if re.match(r"^0\d+$", mobile):
            return f"{self.COUNTRY_CODE}{mobile[1:]}"

        return mobile