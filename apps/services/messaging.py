import json
import logging
import requests

from decouple import config
from django.conf import settings

logger = logging.getLogger(__name__)


class MessagingService:
    TOKEN_BASE_URL = "https://api.orange.com/oauth/v3/token"
    SMS_BASE_URL = (
        "https://api.orange.com/smsmessaging/v1/"
        "outbound/tel%3A%2B224622731178/requests"
    )
    SENDER_ADDRESS = "tel:+224622731178"

    def __init__(self):
        self.orange_token = config("ORANGE_TOKEN", default="")

    def create_token(self):
        """create and return an access token from Orange API"""
        headers_token = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {self.orange_token}",
        }

        response = requests.post(
            self.TOKEN_BASE_URL,
            headers=headers_token,
            data={"grant_type": "client_credentials"},
            timeout=30,
        )

        logger.info("Orange token status: %s", response.status_code)
        logger.info("Orange token response: %s", response.text)

        if response.status_code != 200:
            raise Exception(f"Failed to get Orange token: {response.text}")

        access_token = response.json().get("access_token")

        if not access_token:
            raise Exception("Orange token response does not contain access_token")

        return access_token


    def send_sms(self, recipient, message):
        """Send an SMS using Orange API"""
        access_token = self.create_token()

        recipient = self.cast_mobile(recipient)

        payload = {
            "outboundSMSMessageRequest": {
                "address": f"tel:{recipient}",
                "senderAddress": self.SENDER_ADDRESS,
                "outboundSMSTextMessage": {
                    "message": message
                },
            }
        }

        headers_sms = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}",
        }

        response = requests.post(
            self.SMS_BASE_URL,
            json=payload,
            headers=headers_sms,
            timeout=30,
        )

        logger.info("Orange SMS status: %s", response.status_code)
        logger.info("Orange SMS response: %s", response.text)

        response_data = response.json() if response.text else {}

        if response.status_code not in [200, 201]:
            return {
                "error": True,
                "success": False,
                "message": "Failed to send SMS",
                "status_code": response.status_code,
                "response": response_data,
            }

        return {
            "error": False,
            "success": True,
            "message": "SMS sent successfully",
            "status_code": response.status_code,
            "response": response_data,
        }


    def cast_mobile(self, mobile):
        """Normalize a mobile number to the format +224XXXXXXXXX"""
        mobile = str(mobile).strip().replace(" ", "")

        if mobile.startswith("+224"):
            return mobile

        if mobile.startswith("224"):
            return f"+{mobile}"

        if mobile.startswith("0"):
            return f"+224{mobile[1:]}"

        if len(mobile) == 9:
            return f"+224{mobile}"

        return mobile