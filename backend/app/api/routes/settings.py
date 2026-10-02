from fastapi import APIRouter
from typing import Dict, Any, Optional
from app.schemas.settings import SystemSettingsSchema, SystemSettingsUpdate, PromptTestRequest, PromptTestResponse
from app.database.supabase_client import db_service, in_memory_db
from app.services.ai_service import ai_service
from app.core.config import settings
from app.core.logging import logger
from app.services.redis_service import redis_service

router = APIRouter(prefix="/settings", tags=["Settings"])

@router.get("", response_model=SystemSettingsSchema)
async def get_settings():
    """
    Get current AI model, embedding, and RAG configuration.
    """
    client = db_service.get_client()
    if db_service.is_connected and client:
        try:
            res = client.table("system_settings").select("*").eq("id", "default").execute()
            if res.data:
                return res.data[0]
        except Exception:
            pass
    return in_memory_db.system_settings

@router.patch("", response_model=SystemSettingsSchema)
async def update_settings(payload: SystemSettingsUpdate):
    """
    Update AI model parameters, RAG top_k, threshold, or system prompt.
    """
    update_data = {k: v for k, v in payload.dict().items() if v is not None}
    
    client = db_service.get_client()
    if db_service.is_connected and client:
        try:
            client.table("system_settings").update(update_data).eq("id", "default").execute()
        except Exception:
            pass

    in_memory_db.system_settings.update(update_data)
    return in_memory_db.system_settings

@router.post("/toggle-bot")
async def toggle_bot(payload: Optional[Dict[str, Any]] = None):
    """
    Toggle the master AI bot switch on or off.
    If 'bot_enabled' is passed in payload, sets to that value; otherwise inverts current state.
    """
    current_status = in_memory_db.system_settings.get("bot_enabled", True)
    if payload and "bot_enabled" in payload and payload["bot_enabled"] is not None:
        new_status = bool(payload["bot_enabled"])
    else:
        new_status = not current_status

    in_memory_db.system_settings["bot_enabled"] = new_status

    client = db_service.get_client()
    if db_service.is_connected and client:
        try:
            client.table("system_settings").update({"bot_enabled": new_status}).eq("id", "default").execute()
        except Exception:
            pass

    return {
        "bot_enabled": new_status,
        "status": "active" if new_status else "paused",
        "message": "AI Bot activated (Auto-replies ON)" if new_status else "AI Bot paused (Manual Human Mode ON)"
    }

@router.post("/test-playground", response_model=PromptTestResponse)
async def test_prompt_playground(payload: PromptTestRequest):
    """
    Interactive RAG & AI Prompt Playground:
    Allows administrators to test queries directly against the knowledge base,
    inspecting rewritten queries, retrieved chunks, similarity scores, and responses.
    """
    result = await ai_service.generate_support_response(
        query=payload.query,
        conversation_history=payload.conversation_history,
        top_k=payload.top_k or in_memory_db.system_settings.get("top_k", 5),
        similarity_threshold=payload.similarity_threshold or in_memory_db.system_settings.get("similarity_threshold", 0.35)
    )

    rag = result["rag_result"]
    return {
        "query": payload.query,
        "rewritten_query": rag.get("rewritten_query", payload.query),
        "retrieved_chunks": rag.get("chunks", []),
        "generated_response": result["response"],
        "similarity_scores": rag.get("similarity_scores", []),
        "model_used": result["model"],
        "latency_ms": result["latency_ms"],
        "grounded": rag.get("is_relevant", False)
    }

@router.post("/reset-all-data")
async def reset_all_data():
    """
    Purges all customer conversations, messages, customer profiles, handoffs, and analytics caches.
    Resets dashboard counters to 0.
    """
    # 1. Clear in-memory database
    in_memory_db.conversations.clear()
    in_memory_db.messages.clear()
    in_memory_db.customers.clear()
    in_memory_db.human_handoffs.clear()
    in_memory_db.ai_logs.clear()

    # 2. Invalidate Redis caches
    try:
        await redis_service.delete("cache:analytics:summary")
        r_client = await redis_service.get_client()
        if r_client:
            keys = await r_client.keys("whatsapp:gateway:dedup:*")
            if keys:
                await r_client.delete(*keys)
    except Exception as e:
        logger.warning(f"Error purging redis cache: {e}")

    # 3. Purge Supabase records if connected
    client = db_service.get_client()
    if db_service.is_connected and client:
        try:
            client.table("messages").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
            client.table("conversations").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
            client.table("customers").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
            client.table("human_handoffs").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
            client.table("ai_logs").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        except Exception as e:
            logger.warning(f"Error purging Supabase records: {e}")

    logger.info("Admin reset triggered: all chat history and customer data reset to 0.")
    return {
        "success": True,
        "message": "All chat history, customers, and analytics data successfully reset to 0."
    }

