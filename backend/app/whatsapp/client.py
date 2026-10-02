import httpx
from typing import Optional, Dict, Any
from app.core.config import settings
from app.core.logging import logger

class WhatsAppClient:
    """
    Unified WhatsApp Gateway Client supporting:
    1. Meta WhatsApp Business Cloud API (Official)
    2. OpenWA Gateway (Self-hosted WhatsApp bridge https://github.com/rmyndharis/OpenWA)
    3. Simulated mode for testing & offline development
    """
    def __init__(self):
        self.gateway = settings.WHATSAPP_GATEWAY.lower()
        self.phone_number_id = settings.WHATSAPP_PHONE_NUMBER_ID
        self.access_token = settings.WHATSAPP_ACCESS_TOKEN
        self.version = settings.WHATSAPP_API_VERSION
        self.base_url = f"https://graph.facebook.com/{self.version}/{self.phone_number_id}"
        
        # OpenWA settings
        self.openwa_url = settings.OPENWA_API_URL.rstrip('/')
        self.openwa_key = settings.OPENWA_API_KEY
        self.openwa_session = settings.OPENWA_SESSION

    @property
    def is_configured(self) -> bool:
        if self.gateway == "openwa":
            return bool(self.openwa_url)
        return bool(self.phone_number_id and self.access_token and not self.access_token.startswith("your_"))

    async def send_text_message(self, to_phone_number: str, text: str) -> Dict[str, Any]:
        """
        Sends an outbound text message to a customer's WhatsApp number via Meta Cloud API or OpenWA.
        """
        dest = to_phone_number.strip()
        clean_phone = dest if "@" in dest else "".join(filter(str.isdigit, dest))

        # 1. Attempt sending through Baileys gateway if running
        try:
            gateway_endpoint = f"{settings.WHATSAPP_GATEWAY_URL.rstrip('/')}/api/send"
            async with httpx.AsyncClient(timeout=6.0) as http_client:
                res = await http_client.post(gateway_endpoint, json={"to": clean_phone, "message": text})
                if res.status_code == 200:
                    logger.info(f"WhatsApp message dispatched via Baileys Gateway ({gateway_endpoint}) to {clean_phone}")
                    return res.json()
        except Exception:
            pass

        # 2. Check if gateway is OpenWA
        if self.gateway == "openwa":
            return await self._send_openwa_message(clean_phone, text)

        # Meta WhatsApp Cloud API
        if not self.is_configured:
            logger.info(f"[SIMULATED WHATSAPP OUTBOUND] To: {clean_phone} | Message: {text}")
            return {
                "messaging_product": "whatsapp",
                "contacts": [{"input": clean_phone, "wa_id": clean_phone}],
                "messages": [{"id": f"wamid.simulated.{clean_phone}"}],
                "simulated": True
            }

        url = f"{self.base_url}/messages"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": clean_phone,
            "type": "text",
            "text": {"preview_url": False, "body": text}
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(url, headers=headers, json=payload)
                response_data = response.json()
                if response.status_code >= 400:
                    logger.error(f"WhatsApp Cloud API Error ({response.status_code}): {response_data}")
                    return {"error": response_data, "status_code": response.status_code}
                
                logger.info(f"WhatsApp message sent successfully via Meta Cloud API to {clean_phone}")
                return response_data
        except Exception as e:
            logger.error(f"Failed to communicate with WhatsApp API: {e}")
            return {"error": str(e)}

    async def _send_openwa_message(self, clean_phone: str, text: str) -> Dict[str, Any]:
        """
        Sends message through self-hosted OpenWA gateway (https://github.com/rmyndharis/OpenWA).
        Supports chatId format (e.g. 923001234567@c.us).
        """
        chat_id = f"{clean_phone}@c.us" if not clean_phone.endswith("@c.us") else clean_phone
        endpoints = [
            f"{self.openwa_url}/api/sendText",
            f"{self.openwa_url}/api/{self.openwa_session}/send-message",
            f"{self.openwa_url}/api/messages/send"
        ]
        headers = {"Content-Type": "application/json"}
        if self.openwa_key:
            headers["Authorization"] = f"Bearer {self.openwa_key}"
            headers["x-api-key"] = self.openwa_key

        payload = {
            "chatId": chat_id,
            "to": chat_id,
            "phone": clean_phone,
            "content": text,
            "text": text,
            "message": text
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                for ep in endpoints:
                    try:
                        resp = await client.post(ep, headers=headers, json=payload)
                        if resp.status_code in [200, 201]:
                            logger.info(f"OpenWA message delivered via {ep} to {chat_id}")
                            return resp.json() if resp.text.startswith("{") else {"status": "success", "raw": resp.text}
                    except httpx.HTTPError:
                        continue

            logger.info(f"[SIMULATED OPENWA OUTBOUND] (OpenWA server at {self.openwa_url} not reachable) To: {chat_id} | Message: {text}")
            return {"status": "simulated", "gateway": "openwa", "chatId": chat_id}
        except Exception as e:
            logger.error(f"OpenWA gateway communication failed: {e}")
            return {"error": str(e), "gateway": "openwa"}

    async def mark_message_as_read(self, message_id: str) -> bool:
        """
        Sends read receipt for incoming WhatsApp message.
        """
        if not self.is_configured or not message_id or message_id.startswith("wamid.simulated") or message_id.startswith("openwa_"):
            return True

        if self.gateway == "openwa":
            return True

        url = f"{self.base_url}/messages"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        payload = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id
        }

        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                resp = await client.post(url, headers=headers, json=payload)
                return resp.status_code == 200
        except Exception as e:
            logger.warning(f"Failed to mark WhatsApp message {message_id} as read: {e}")
            return False

whatsapp_client = WhatsAppClient()
