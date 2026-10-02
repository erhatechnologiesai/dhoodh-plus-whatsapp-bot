from typing import Optional, List, Dict, Any
from app.core.config import settings
from app.core.logging import logger
import math
import uuid
from datetime import datetime

try:
    from supabase import create_client, Client
except ImportError:
    create_client = None
    Client = Any

# Mock/In-Memory fallback store for testing or offline development
class InMemoryDatabase:
    def __init__(self):
        self.documents: Dict[str, Dict[str, Any]] = {}
        self.document_chunks: Dict[str, Dict[str, Any]] = {}
        self.customers: Dict[str, Dict[str, Any]] = {}
        self.conversations: Dict[str, Dict[str, Any]] = {}
        self.messages: Dict[str, Dict[str, Any]] = {}
        self.ai_logs: Dict[str, Dict[str, Any]] = {}
        self.human_handoffs: Dict[str, Dict[str, Any]] = {}
        self.system_settings: Dict[str, Any] = {
            "id": "default",
            "llm_provider": settings.LLM_PROVIDER,
            "llm_model": settings.LLM_MODEL,
            "embedding_provider": settings.EMBEDDING_PROVIDER,
            "embedding_model": settings.EMBEDDING_MODEL,
            "embedding_dimension": settings.EMBEDDING_DIMENSION,
            "temperature": settings.LLM_TEMPERATURE,
            "top_k": settings.RAG_TOP_K,
            "similarity_threshold": settings.RAG_SIMILARITY_THRESHOLD,
            "max_context_tokens": settings.MAX_CONTEXT_TOKENS,
            "system_prompt": (
                "You are the natural WhatsApp customer assistant for Allah Ho Traders (Doodh Plus). "
                "Primary Directives: Understand user intent from COMPLETE conversation history, not only the latest message. "
                "Always resolve references ('ye', 'wo', 'iska', 'iski', 'uska', 'isko', 'that', 'this') using conversation context. "
                "Strict Relevance: Answer ONLY and EXACTLY what the user asks in their message or voice note. Do not introduce unasked topics. "
                "Strict Grounding: Use ONLY verified information from the knowledge base. Never invent prices or specifications. "
                "Animal Dosages: Large animals (Cow, Buffalo) = 100g daily in feed/wanda; Small animals (Goat, Sheep, Calves) = 20-30g daily. "
                "Packages & Prices: 1kg = Rs. 1,750, 10kg = Rs. 12,500. Free Home Delivery & Cash on Delivery across Pakistan. "
                "Keep responses natural, human-like, polite, 2 to 5 short lines, without emojis, matching the user's language (Roman Urdu, Urdu, English)."
            ),
            "human_handoff_keywords": [
                "agent", "human", "representative", "operator", "insan se baat", "admin", "support person"
            ],
            "bot_enabled": True,
            "updated_at": datetime.utcnow().isoformat()
        }

    def cosine_similarity(self, v1: List[float], v2: List[float]) -> float:
        if not v1 or not v2 or len(v1) != len(v2):
            return 0.0
        dot = sum(a * b for a, b in zip(v1, v2))
        norm1 = math.sqrt(sum(a * a for a in v1))
        norm2 = math.sqrt(sum(b * b for b in v2))
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot / (norm1 * norm2)

    def match_chunks(self, query_embedding: List[float], match_threshold: float = 0.35, match_count: int = 5, filter_doc_id: Optional[str] = None) -> List[Dict[str, Any]]:
        results = []
        for chunk_id, chunk in self.document_chunks.items():
            if filter_doc_id and str(chunk.get("document_id")) != str(filter_doc_id):
                continue
            emb = chunk.get("embedding")
            if not emb:
                continue
            sim = self.cosine_similarity(query_embedding, emb)
            if sim >= match_threshold:
                chunk_copy = dict(chunk)
                chunk_copy["similarity"] = round(float(sim), 4)
                results.append(chunk_copy)
        # Sort descending by similarity
        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:match_count]

in_memory_db = InMemoryDatabase()

class SupabaseService:
    def __init__(self):
        self.client: Optional[Client] = None
        self.is_connected = False
        
        if settings.SUPABASE_URL and settings.SUPABASE_SERVICE_ROLE_KEY and create_client:
            try:
                self.client = create_client(
                    settings.SUPABASE_URL,
                    settings.SUPABASE_SERVICE_ROLE_KEY
                )
                self.is_connected = True
                logger.info("Supabase client initialized successfully with live service-role credentials")
            except Exception as e:
                logger.warning(f"Failed to connect to Supabase: {e}. Falling back to in-memory store.")
                self.is_connected = False
        else:
            logger.info("Supabase credentials not configured or incomplete. Operating with in-memory database adapter.")

    def get_client(self) -> Optional[Client]:
        return self.client

db_service = SupabaseService()
