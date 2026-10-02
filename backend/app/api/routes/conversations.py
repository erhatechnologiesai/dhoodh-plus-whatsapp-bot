from fastapi import APIRouter, HTTPException, Query, status
from typing import List, Optional
from app.services.conversation_service import conversation_service
from app.schemas.conversation import ConversationResponse, MessageResponse, SendMessageRequest, UpdateConversationRequest

router = APIRouter(prefix="/conversations", tags=["Conversations"])

@router.get("", response_model=List[ConversationResponse])
async def list_conversations(status: Optional[str] = Query(None)):
    """
    List all customer conversations with latest message preview and status filter.
    """
    return await conversation_service.list_conversations(status=status)

@router.get("/{conversation_id}/messages", response_model=List[MessageResponse])
async def get_conversation_messages(conversation_id: str):
    """
    Get all messages for a specific conversation in chronological order.
    """
    return await conversation_service.get_conversation_messages(conversation_id)

@router.post("/{conversation_id}/messages")
async def send_agent_message(conversation_id: str, payload: SendMessageRequest):
    """
    Human agent sends a message from Admin Dashboard.
    Persists to database and sends message directly to customer WhatsApp.
    """
    result = await conversation_service.send_agent_message(
        conversation_id=conversation_id,
        content=payload.content,
        role=payload.role
    )
    return result

@router.patch("/{conversation_id}")
async def update_conversation(conversation_id: str, payload: UpdateConversationRequest):
    """
    Update conversation status (ACTIVE, HUMAN_HANDOFF, CLOSED) or toggle AI on/off.
    """
    updated = await conversation_service.update_conversation(
        conversation_id=conversation_id,
        status=payload.status,
        ai_enabled=payload.ai_enabled,
        assigned_agent=payload.assigned_agent
    )
    return updated
