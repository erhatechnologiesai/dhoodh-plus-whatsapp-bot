from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class DailyMessageCount(BaseModel):
    date: str
    incoming: int
    outgoing: int

class AnalyticsSummary(BaseModel):
    total_customers: int
    total_conversations: int
    total_messages: int
    active_conversations: int
    ai_resolved_conversations: int
    human_handoffs: int
    ready_documents: int
    total_knowledge_chunks: int
    average_latency_ms: float
    retrieval_success_rate: float
    daily_messages: List[DailyMessageCount] = []
