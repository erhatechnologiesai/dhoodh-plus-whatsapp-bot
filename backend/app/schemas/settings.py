from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class SystemSettingsSchema(BaseModel):
    id: str = "default"
    llm_provider: str = "openai"
    llm_model: str = "gpt-4o-mini"
    embedding_provider: str = "openai"
    embedding_model: str = "text-embedding-3-small"
    embedding_dimension: int = 1536
    temperature: float = 0.2
    top_k: int = 5
    similarity_threshold: float = 0.35
    max_context_tokens: int = 3000
    system_prompt: str
    bot_enabled: bool = True
    human_handoff_keywords: List[str] = [
        "agent", "human", "representative", "operator", "insan se baat", "admin", "support person"
    ]
    updated_at: Optional[datetime] = None

class SystemSettingsUpdate(BaseModel):
    bot_enabled: Optional[bool] = None
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    embedding_provider: Optional[str] = None
    embedding_model: Optional[str] = None
    embedding_dimension: Optional[int] = None
    temperature: Optional[float] = None
    top_k: Optional[int] = None
    similarity_threshold: Optional[float] = None
    max_context_tokens: Optional[int] = None
    system_prompt: Optional[str] = None
    human_handoff_keywords: Optional[List[str]] = None

class PromptTestRequest(BaseModel):
    query: str
    conversation_history: Optional[List[Dict[str, str]]] = []
    top_k: Optional[int] = None
    similarity_threshold: Optional[float] = None

class PromptTestResponse(BaseModel):
    query: str
    rewritten_query: str
    retrieved_chunks: List[Dict[str, Any]]
    generated_response: str
    similarity_scores: List[float]
    model_used: str
    latency_ms: float
    grounded: bool
