from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID

class CustomerBase(BaseModel):
    whatsapp_number: str
    name: Optional[str] = None
    email: Optional[str] = None
    metadata: Dict[str, Any] = {}

class CustomerCreate(CustomerBase):
    pass

class CustomerResponse(CustomerBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    total_messages: Optional[int] = 0
    active_conversation_id: Optional[UUID] = None
