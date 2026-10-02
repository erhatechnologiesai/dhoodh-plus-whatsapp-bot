from fastapi import APIRouter
from app.core.config import settings
from app.database.supabase_client import db_service
from app.whatsapp.client import whatsapp_client
from app.services.redis_service import redis_service

router = APIRouter(prefix="/health", tags=["Health"])

@router.get("")
async def health_check():
    """
    Check system health, Supabase status, Redis status, and WhatsApp integration readiness.
    """
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "environment": settings.ENV,
        "supabase_connected": db_service.is_connected,
        "whatsapp_configured": whatsapp_client.is_configured,
        "redis": await redis_service.get_status(),
        "llm_provider": settings.LLM_PROVIDER,
        "embedding_provider": settings.EMBEDDING_PROVIDER
    }

