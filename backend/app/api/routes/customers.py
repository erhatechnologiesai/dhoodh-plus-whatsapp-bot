from fastapi import APIRouter
from typing import List
from app.services.conversation_service import conversation_service
from app.schemas.customer import CustomerResponse

router = APIRouter(prefix="/customers", tags=["Customers"])

@router.get("", response_model=List[CustomerResponse])
async def list_customers():
    """
    List all WhatsApp customers.
    """
    return await conversation_service.list_customers()
