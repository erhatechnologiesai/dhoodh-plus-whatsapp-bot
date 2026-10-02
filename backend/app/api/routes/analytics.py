from fastapi import APIRouter
from app.schemas.analytics import AnalyticsSummary
from app.services.analytics_service import analytics_service

router = APIRouter(prefix="/analytics", tags=["Analytics"])

@router.get("/summary", response_model=AnalyticsSummary)
async def get_analytics_summary():
    """
    Get aggregated system statistics, daily message counts, and RAG performance.
    """
    return await analytics_service.get_summary()
