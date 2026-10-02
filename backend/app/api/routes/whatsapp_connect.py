from fastapi import APIRouter, HTTPException, Query, Body
from typing import Dict, Any, Optional
from pydantic import BaseModel
import uuid
import time
from app.core.config import settings
from app.whatsapp.client import whatsapp_client
from app.services.whatsapp_service import whatsapp_service
from app.services.voice_service import voice_service
from app.services.ai_service import get_next_unclear_voice_apology
from app.core.logging import logger
from app.database.supabase_client import in_memory_db, db_service
from app.services.redis_service import redis_service

router = APIRouter(prefix="/whatsapp/connect", tags=["WhatsApp Connect"])

class OnConnectedRequest(BaseModel):
    phone: str
    name: Optional[str] = "WhatsApp Connected"

class TestMessageRequest(BaseModel):
    phone: str
    message: str

class SimulateInboundRequest(BaseModel):
    phone: str
    message: str
    sender_name: Optional[str] = "Farm Owner"
    remote_jid: Optional[str] = None

class VoiceInboundRequest(BaseModel):
    phone: str
    audio_base64: str
    sender_name: Optional[str] = "Customer"
    extension: Optional[str] = "ogg"
    remote_jid: Optional[str] = None

# In-memory connection state
connection_state = {
    "gateway": settings.WHATSAPP_GATEWAY,
    "status": "ready_to_scan",  # "ready_to_scan", "connected", "offline"
    "connected_phone": None,
    "connected_name": None,
    "last_synced": None,
    "qr_seed": str(uuid.uuid4())[:8]
}

@router.get("/status")
async def get_connection_status():
    """
    Returns live WhatsApp QR connection status and QR code data.
    """
    try:
        redis_status = await redis_service.get("whatsapp:gateway:status")
        redis_phone = await redis_service.get("whatsapp:gateway:phone")
        if redis_status:
            connection_state["status"] = redis_status
            if redis_status == "connected" and redis_phone:
                connection_state["connected_phone"] = redis_phone
            elif redis_status != "connected":
                connection_state["connected_phone"] = None
    except Exception:
        pass

    is_connected = connection_state["status"] == "connected" and bool(connection_state["connected_phone"])
    # Generate live WhatsApp Web standard QR string
    qr_data = f"2@dhoodplus_{connection_state['qr_seed']},{int(time.time())},DhoodhPlusAI"
    # Public QR image render URL
    qr_image_url = f"https://api.qrserver.com/v1/create-qr-code/?size=260x260&margin=10&data={qr_data}"

    return {
        "gateway": settings.WHATSAPP_GATEWAY,
        "status": connection_state["status"] if is_connected else "disconnected",
        "connected": is_connected,
        "phone": connection_state["connected_phone"] if is_connected else None,
        "name": connection_state["connected_name"] if is_connected else None,
        "qr_data": qr_data,
        "qr_image_url": qr_image_url,
        "webhook_url": f"http://{settings.HOST}:{settings.PORT}/api/whatsapp/webhook",
        "openwa_url": settings.OPENWA_API_URL
    }

@router.post("/refresh-qr")
async def refresh_qr():
    """
    Regenerates a new QR code session.
    """
    connection_state["qr_seed"] = str(uuid.uuid4())[:8]
    connection_state["status"] = "ready_to_scan"
    return await get_connection_status()

@router.post("/on-connected")
async def on_connected(payload: OnConnectedRequest):
    """
    Called by WhatsApp gateway when a connection opens.
    If a new/different phone number connects, automatically resets old data so the dashboard starts from 0 for the new number.
    """
    clean_phone = "".join(filter(str.isdigit, payload.phone))
    old_phone = connection_state.get("connected_phone")
    
    connection_state["status"] = "connected"
    connection_state["connected_phone"] = clean_phone
    connection_state["connected_name"] = payload.name or "Official Farm WhatsApp"
    connection_state["last_synced"] = time.strftime("%Y-%m-%d %H:%M:%S")

    reset_triggered = False
    if clean_phone and clean_phone != old_phone:
        logger.info(f"New WhatsApp number linked (+{clean_phone}). Resetting old conversation data to 0...")
        in_memory_db.conversations.clear()
        in_memory_db.messages.clear()
        in_memory_db.customers.clear()
        in_memory_db.human_handoffs.clear()
        in_memory_db.ai_logs.clear()
        await redis_service.delete("cache:analytics:summary")
        reset_triggered = True

    return {
        "status": "connected",
        "phone": clean_phone,
        "reset": reset_triggered,
        "message": f"Device +{clean_phone} connected successfully!"
    }

@router.post("/link-device")
async def link_device(phone: str = Body(..., embed=True), name: Optional[str] = Body("Official Farm WhatsApp", embed=True)):
    """
    Sets phone as linked device.
    If phone number is changed, automatically resets previous conversation and customer data to 0.
    """
    clean_phone = "".join(filter(str.isdigit, phone))
    old_phone = connection_state.get("connected_phone")
    connection_state["status"] = "connected"
    connection_state["connected_phone"] = clean_phone
    connection_state["connected_name"] = name
    connection_state["last_synced"] = time.strftime("%Y-%m-%d %H:%M:%S")

    if clean_phone and clean_phone != old_phone:
        logger.info(f"Device changed to +{clean_phone}. Resetting old conversation data to 0...")
        in_memory_db.conversations.clear()
        in_memory_db.messages.clear()
        in_memory_db.customers.clear()
        in_memory_db.human_handoffs.clear()
        in_memory_db.ai_logs.clear()
        await redis_service.delete("cache:analytics:summary")

    logger.info(f"WhatsApp device linked successfully to: +{clean_phone} ({name})")
    return {"message": f"Device +{clean_phone} linked successfully!", "state": connection_state}

@router.post("/disconnect")
async def disconnect_device():
    """
    Disconnects the active WhatsApp session and clears connected phone.
    """
    connection_state["status"] = "disconnected"
    connection_state["connected_phone"] = None
    connection_state["connected_name"] = None
    try:
        await redis_service.set("whatsapp:gateway:status", "disconnected")
        await redis_service.delete("whatsapp:gateway:phone")
    except Exception:
        pass
    return {"message": "WhatsApp device unlinked successfully."}

@router.post("/send-test")
async def send_test_message(payload: TestMessageRequest):
    """
    Sends an outbound test message to a customer's WhatsApp number.
    """
    clean_phone = "".join(filter(str.isdigit, payload.phone))
    res = await whatsapp_client.send_text_message(clean_phone, payload.message)
    return {"status": "sent", "phone": clean_phone, "result": res}

@router.post("/simulate-inbound")
async def simulate_inbound_message(payload: SimulateInboundRequest):
    """
    Simulates an incoming WhatsApp message from a phone number,
    running through RAG vector retrieval, AI generation, and returning the exact answer.
    """
    msg_id = f"wamid.test.{uuid.uuid4().hex[:8]}"
    res = await whatsapp_service.process_incoming_message(
        from_phone=payload.phone,
        message_body=payload.message,
        whatsapp_message_id=msg_id,
        sender_name=payload.sender_name,
        skip_outbound=True
    )
    reply_text = res.get("response") or res.get("reply") or ""
    return {
        "status": "responded",
        "conversation_id": res.get("conversation_id"),
        "response": reply_text,
        "ai_reply": reply_text,
        "whatsapp_response": res.get("whatsapp_response")
    }

@router.post("/voice")
async def process_voice_message(payload: VoiceInboundRequest):
    """
    Receives voice note/audio from WhatsApp, transcribes speech in Urdu/English,
    queries Doodh Plus Knowledge Engine (PDF RAG), and returns the generated answer.
    """
    clean_phone = "".join(filter(str.isdigit, payload.phone))
    
    # 1. Listen & Transcribe
    transcription_result = voice_service.process_voice_payload(
        audio_base64=payload.audio_base64,
        extension=payload.extension or "ogg"
    )
    
    transcribed_text = transcription_result.get("text")
    if not transcribed_text:
        fallback_reply = get_next_unclear_voice_apology()
        return {
            "status": "voice_unclear",
            "transcribed_text": None,
            "response": fallback_reply,
            "ai_reply": fallback_reply
        }
    
    logger.info(f"[Inbound WhatsApp Voice] From +{clean_phone} ({payload.sender_name}): Transcribed='{transcribed_text}'")
    
    # 2. Process query via WhatsApp service with PDF knowledge base
    msg_id = f"wamid.voice.{uuid.uuid4().hex[:8]}"
    res = await whatsapp_service.process_incoming_message(
        from_phone=clean_phone,
        message_body=transcribed_text,
        whatsapp_message_id=msg_id,
        sender_name=payload.sender_name,
        is_voice=True,
        skip_outbound=True
    )
    
    reply_text = res.get("response") or res.get("reply") or ""
    return {
        "status": "responded",
        "transcribed_text": transcribed_text,
        "conversation_id": res.get("conversation_id"),
        "response": reply_text,
        "ai_reply": reply_text,
        "whatsapp_response": res.get("whatsapp_response")
    }

