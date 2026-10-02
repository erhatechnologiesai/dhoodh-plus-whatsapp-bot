from fastapi import APIRouter, Request, Response, Query, HTTPException, status
from app.core.config import settings
from app.core.logging import logger
from app.services.whatsapp_service import whatsapp_service
import json

router = APIRouter(prefix="/whatsapp", tags=["WhatsApp"])

@router.get("/webhook")
async def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
    hub_verify_token: str = Query(None, alias="hub.verify_token")
):
    """
    Meta WhatsApp Cloud API Webhook Verification Endpoint.
    Responds to Meta's GET challenge when configuring webhook in developer portal.
    """
    challenge = whatsapp_service.verify_webhook(hub_mode, hub_verify_token, hub_challenge)
    if challenge:
        return Response(content=challenge, media_type="text/plain")
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Verification failed")

@router.post("/webhook")
async def handle_whatsapp_webhook(request: Request):
    """
    Universal WhatsApp Webhook Event Receiver:
    Supports both Meta WhatsApp Business Cloud API and self-hosted OpenWA gateway (https://github.com/rmyndharis/OpenWA).
    """
    try:
        body_bytes = await request.body()
        payload = json.loads(body_bytes.decode("utf-8"))
        logger.info(f"Incoming WhatsApp webhook payload: {payload}")

        # CASE 1: Meta Official WhatsApp Cloud API Payload
        if payload.get("object") == "whatsapp_business_account":
            entries = payload.get("entry", [])
            for entry in entries:
                changes = entry.get("changes", [])
                for change in changes:
                    value = change.get("value", {})
                    messages = value.get("messages", [])
                    contacts = value.get("contacts", [])
                    
                    sender_name = None
                    if contacts and len(contacts) > 0:
                        sender_name = contacts[0].get("profile", {}).get("name")

                    for msg in messages:
                        msg_type = msg.get("type")
                        msg_id = msg.get("id")
                        from_phone = msg.get("from")

                        if msg_type == "text" and "text" in msg:
                            body_text = msg["text"].get("body", "").strip()
                            if body_text and from_phone and msg_id:
                                await whatsapp_service.process_incoming_message(
                                    from_phone=from_phone,
                                    message_body=body_text,
                                    whatsapp_message_id=msg_id,
                                    sender_name=sender_name
                                )
            return {"status": "success", "gateway": "meta"}

        # CASE 2: OpenWA Gateway Payload (https://github.com/rmyndharis/OpenWA)
        # OpenWA formats: { "event": "message", "data": { ... } } or { "body": "...", "from": "..." }
        openwa_data = payload.get("data", payload)
        if isinstance(openwa_data, dict):
            # Check if this is an incoming message (not sent from bot itself)
            is_from_me = openwa_data.get("fromMe", False)
            if not is_from_me:
                from_field = openwa_data.get("from", openwa_data.get("sender", {}).get("id", ""))
                # Strip @c.us or @s.whatsapp.net
                clean_phone = "".join(filter(str.isdigit, str(from_field)))
                body_text = openwa_data.get("body", openwa_data.get("text", openwa_data.get("content", "")))
                msg_id = openwa_data.get("id", f"openwa_{clean_phone}_{hash(body_text)}")
                sender_name = openwa_data.get("notifyName", openwa_data.get("sender", {}).get("pushname"))

                if clean_phone and body_text:
                    await whatsapp_service.process_incoming_message(
                        from_phone=clean_phone,
                        message_body=str(body_text).strip(),
                        whatsapp_message_id=str(msg_id),
                        sender_name=sender_name
                    )
                    return {"status": "success", "gateway": "openwa"}

        return {"status": "ignored"}

    except Exception as e:
        logger.error(f"Error handling WhatsApp webhook: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}
