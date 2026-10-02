from typing import List, Dict, Any, Optional, Tuple
from app.embeddings.provider import get_embedding_provider
from app.rag.query_rewriter import QueryRewriter
from app.database.supabase_client import db_service, in_memory_db
from app.core.config import settings
from app.core.logging import logger
import time

class RAGService:
    """
    Dedicated RAG Service handling embedding generation, pgvector search,
    context assembly, relevance filtering, and source tracking.
    """

    def __init__(self):
        self.embedding_provider = get_embedding_provider()

    async def create_embedding(self, text: str) -> List[float]:
        return await self.embedding_provider.embed_query(text)

    async def search_knowledge(
        self,
        query: str,
        top_k: Optional[int] = None,
        threshold: Optional[float] = None,
        filter_doc_id: Optional[str] = None
    ) -> Tuple[List[Dict[str, Any]], float]:
        """
        Executes pgvector similarity search against Supabase RPC or in-memory vector store.
        Returns matching chunks and retrieval latency.
        """
        start_time = time.time()
        k = top_k or settings.RAG_TOP_K
        thresh = threshold if threshold is not None else settings.RAG_SIMILARITY_THRESHOLD

        query_embedding = await self.create_embedding(query)
        client = db_service.get_client()

        retrieved_chunks: List[Dict[str, Any]] = []

        if db_service.is_connected and client:
            try:
                rpc_params = {
                    "query_embedding": query_embedding,
                    "match_threshold": float(thresh),
                    "match_count": int(k)
                }
                if filter_doc_id:
                    rpc_params["filter_doc_id"] = filter_doc_id

                resp = client.rpc("match_document_chunks", rpc_params).execute()
                retrieved_chunks = resp.data or []
            except Exception as e:
                logger.error(f"Error querying Supabase pgvector RPC: {e}. Falling back to in-memory store.")
                retrieved_chunks = in_memory_db.match_chunks(
                    query_embedding=query_embedding,
                    match_threshold=thresh,
                    match_count=k,
                    filter_doc_id=filter_doc_id
                )
        else:
            # Query in-memory vector database
            retrieved_chunks = in_memory_db.match_chunks(
                query_embedding=query_embedding,
                match_threshold=thresh,
                match_count=k,
                filter_doc_id=filter_doc_id
            )

        latency = round((time.time() - start_time) * 1000, 2)
        logger.info(f"RAG search found {len(retrieved_chunks)} chunks with threshold >= {thresh} in {latency}ms")
        return retrieved_chunks, latency

    def calculate_relevance(self, chunks: List[Dict[str, Any]], threshold: float) -> bool:
        if not chunks:
            return False
        # If top chunk similarity meets threshold, consider knowledge relevant
        top_score = max((c.get("similarity", 0.0) for c in chunks), default=0.0)
        return top_score >= threshold

    def build_context(self, chunks: List[Dict[str, Any]], max_chars: int = 4000) -> str:
        """
        Constructs clean context for LLM with explicit page and source citations.
        """
        if not chunks:
            return ""

        context_parts = []
        accumulated_chars = 0

        for i, chunk in enumerate(chunks, 1):
            doc_name = chunk.get("metadata", {}).get("doc_name", "Official Company Document")
            page_num = chunk.get("page_number", 1)
            sec_title = chunk.get("section_title", "General Information")
            content = chunk.get("content", "").strip()

            snippet = f"[DOCUMENT CHUNK #{i}] (Source: {doc_name}, Page: {page_num}, Section: {sec_title})\n{content}\n"
            if accumulated_chars + len(snippet) > max_chars:
                break
            context_parts.append(snippet)
            accumulated_chars += len(snippet)

        return "\n".join(context_parts)

    async def retrieve_context_for_query(
        self,
        query: str,
        recent_messages: List[Dict[str, str]] = None,
        top_k: Optional[int] = None,
        threshold: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Orchestrates query expansion, vector search, relevance validation, and context construction.
        """
        rewritten = QueryRewriter.rewrite_query_with_context(query, recent_messages)
        search_query = rewritten["search_query"]
        detected_language = rewritten["detected_language"]

        chunks, latency = await self.search_knowledge(
            query=search_query,
            top_k=top_k,
            threshold=threshold
        )

        thresh = threshold if threshold is not None else settings.RAG_SIMILARITY_THRESHOLD
        is_relevant = self.calculate_relevance(chunks, thresh)
        context_text = self.build_context(chunks) if is_relevant else ""

        return {
            "original_query": query,
            "rewritten_query": search_query,
            "detected_language": detected_language,
            "chunks": chunks,
            "is_relevant": is_relevant,
            "context_text": context_text,
            "latency_ms": latency,
            "similarity_scores": [c.get("similarity", 0.0) for c in chunks]
        }

rag_service = RAGService()
