from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID

class MessageResponse(BaseModel):
    id: UUID
    conversation_id: UUID
    role: str  # USER, ASSISTANT, SYSTEM, HUMAN
    content: str
    message_type: str = "text"
    whatsapp_message_id: Optional[str] = None
    metadata: Dict[str, Any] = {}
    created_at: datetime

class ConversationResponse(BaseModel):
    id: UUID
    customer_id: UUID
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    status: str  # ACTIVE, HUMAN_HANDOFF, CLOSED
    assigned_agent: Optional[str] = None
    ai_enabled: bool = True
    last_message: Optional[str] = None
    last_message_at: Optional[datetime] = None
    unread_count: Optional[int] = 0
    created_at: datetime
    updated_at: datetime
    messages: Optional[List[MessageResponse]] = []

class SendMessageRequest(BaseModel):
    content: str
    role: str = "HUMAN"  # HUMAN (admin agent) or ASSISTANT

class UpdateConversationRequest(BaseModel):
    status: Optional[str] = None  # ACTIVE, HUMAN_HANDOFF, CLOSED
    ai_enabled: Optional[bool] = None
    assigned_agent: Optional[str] = None
