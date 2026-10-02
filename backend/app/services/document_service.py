import os
import uuid
import hashlib
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional
from uuid import UUID

from app.core.config import settings
from app.core.logging import logger
from app.rag.extractor import PDFExtractor
from app.rag.chunker import IntelligentChunker
from app.embeddings.provider import get_embedding_provider
from app.database.supabase_client import db_service, in_memory_db

class DocumentService:
    """
    Handles PDF ingestion pipeline:
    Upload -> Hash Verification -> Background Text Extraction ->
    Intelligent Chunking -> Embedding Generation -> Vector Storage -> READY status.
    """

    def __init__(self):
        self.chunker = IntelligentChunker()
        self.embedding_provider = get_embedding_provider()
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    @staticmethod
    def calculate_file_hash(file_bytes: bytes) -> str:
        return hashlib.sha256(file_bytes).hexdigest()

    async def save_uploaded_file(self, filename: str, content: bytes) -> str:
        unique_filename = f"{uuid.uuid4()}_{filename}"
        file_path = os.path.join(settings.UPLOAD_DIR, unique_filename)
        with open(file_path, "wb") as f:
            f.write(content)
        return file_path

    async def create_document_record(
        self,
        name: str,
        filename: str,
        storage_path: str,
        file_hash: str,
        file_size: int
    ) -> Dict[str, Any]:
        doc_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        doc_data = {
            "id": doc_id,
            "name": name,
            "original_filename": filename,
            "storage_path": storage_path,
            "file_hash": file_hash,
            "file_size": file_size,
            "page_count": 0,
            "status": "PROCESSING",
            "processing_error": None,
            "created_at": now,
            "updated_at": now
        }

        client = db_service.get_client()
        if db_service.is_connected and client:
            try:
                res = client.table("documents").insert(doc_data).execute()
                if res.data:
                    return res.data[0]
            except Exception as e:
                logger.error(f"Error inserting document into Supabase: {e}")

        # In-memory store
        in_memory_db.documents[doc_id] = doc_data
        return doc_data

    async def update_document_status(
        self,
        doc_id: str,
        status: str,
        page_count: int = 0,
        chunk_count: int = 0,
        error: Optional[str] = None
    ):
        now = datetime.utcnow().isoformat()
        update_data = {
            "status": status,
            "updated_at": now
        }
        if page_count > 0:
            update_data["page_count"] = page_count
        if error:
            update_data["processing_error"] = error

        client = db_service.get_client()
        if db_service.is_connected and client:
            try:
                client.table("documents").update(update_data).eq("id", doc_id).execute()
            except Exception as e:
                logger.error(f"Error updating document status in Supabase: {e}")

        if doc_id in in_memory_db.documents:
            in_memory_db.documents[doc_id].update(update_data)

    async def process_document_pipeline(self, doc_id: str, file_path: str, doc_name: str):
        """
        Executes background extraction, intelligent chunking, embedding generation,
        and vector insertion.
        """
        try:
            logger.info(f"Starting ingestion pipeline for document {doc_id} ({doc_name})")
            
            # 1. Text & Structural Extraction
            extracted = PDFExtractor.extract_document(file_path)
            page_count = extracted["total_pages"]

            # 2. Intelligent Chunking
            chunks = self.chunker.chunk_extracted_data(
                document_id=UUID(doc_id),
                extracted_data=extracted,
                doc_name=doc_name
            )
            logger.info(f"Generated {len(chunks)} semantic chunks for document {doc_id}")

            # 3. Generate Vector Embeddings
            chunk_texts = [c.content for c in chunks]
            embeddings = await self.embedding_provider.embed_documents(chunk_texts)

            # 4. Store Chunks & Vectors in Database
            chunks_to_insert = []
            for i, chunk in enumerate(chunks):
                chunk_id = str(uuid.uuid4())
                chunk_dict = {
                    "id": chunk_id,
                    "document_id": doc_id,
                    "content": chunk.content,
                    "embedding": embeddings[i] if i < len(embeddings) else None,
                    "page_number": chunk.page_number,
                    "chunk_index": chunk.chunk_index,
                    "section_title": chunk.section_title,
                    "metadata": chunk.metadata,
                    "created_at": datetime.utcnow().isoformat()
                }
                chunks_to_insert.append(chunk_dict)
                # Save to in-memory store
                in_memory_db.document_chunks[chunk_id] = chunk_dict

            # Insert into Supabase if connected
            client = db_service.get_client()
            if db_service.is_connected and client:
                try:
                    # Batch insert
                    batch_size = 50
                    for b_start in range(0, len(chunks_to_insert), batch_size):
                        batch = chunks_to_insert[b_start:b_start + batch_size]
                        client.table("document_chunks").insert(batch).execute()
                except Exception as e:
                    logger.error(f"Error saving chunks to Supabase: {e}")

            # 5. Mark document status as READY
            await self.update_document_status(
                doc_id=doc_id,
                status="READY",
                page_count=page_count,
                chunk_count=len(chunks)
            )
            logger.info(f"Document {doc_id} ingestion completed successfully. Status: READY.")

        except Exception as e:
            logger.error(f"Pipeline failed for document {doc_id}: {e}", exc_info=True)
            await self.update_document_status(
                doc_id=doc_id,
                status="FAILED",
                error=str(e)
            )

    async def list_documents(self) -> List[Dict[str, Any]]:
        client = db_service.get_client()
        if db_service.is_connected and client:
            try:
                res = client.table("documents").select("*").order("created_at", desc=True).execute()
                return res.data or []
            except Exception as e:
                logger.error(f"Error fetching documents from Supabase: {e}")

        # Return from in-memory store
        docs = list(in_memory_db.documents.values())
        docs.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return docs

    async def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        client = db_service.get_client()
        if db_service.is_connected and client:
            try:
                res = client.table("documents").select("*").eq("id", doc_id).execute()
                if res.data:
                    return res.data[0]
            except Exception as e:
                logger.error(f"Error fetching document {doc_id}: {e}")

        return in_memory_db.documents.get(doc_id)

    async def get_document_chunks(self, doc_id: str) -> List[Dict[str, Any]]:
        client = db_service.get_client()
        if db_service.is_connected and client:
            try:
                res = client.table("document_chunks").select("id, document_id, content, page_number, chunk_index, section_title, metadata, created_at").eq("document_id", doc_id).order("chunk_index").execute()
                return res.data or []
            except Exception as e:
                logger.error(f"Error fetching chunks from Supabase: {e}")

        chunks = [c for c in in_memory_db.document_chunks.values() if str(c.get("document_id")) == str(doc_id)]
        chunks.sort(key=lambda x: x.get("chunk_index", 0))
        return chunks

    async def delete_document(self, doc_id: str) -> bool:
        client = db_service.get_client()
        if db_service.is_connected and client:
            try:
                # CASCADE deletes chunks in database
                client.table("documents").delete().eq("id", doc_id).execute()
            except Exception as e:
                logger.error(f"Error deleting document from Supabase: {e}")

        # Clean in-memory
        if doc_id in in_memory_db.documents:
            del in_memory_db.documents[doc_id]
        
        # Delete associated chunks
        chunks_to_delete = [cid for cid, c in in_memory_db.document_chunks.items() if str(c.get("document_id")) == str(doc_id)]
        for cid in chunks_to_delete:
            del in_memory_db.document_chunks[cid]

        return True

    async def reindex_document(self, doc_id: str) -> bool:
        doc = await self.get_document(doc_id)
        if not doc or not doc.get("storage_path"):
            return False

        # Delete existing chunks first
        chunks_to_delete = [cid for cid, c in in_memory_db.document_chunks.items() if str(c.get("document_id")) == str(doc_id)]
        for cid in chunks_to_delete:
            del in_memory_db.document_chunks[cid]

        client = db_service.get_client()
        if db_service.is_connected and client:
            try:
                client.table("document_chunks").delete().eq("document_id", doc_id).execute()
            except Exception as e:
                logger.warning(f"Error clearing chunks in Supabase before re-indexing: {e}")

        # Reset document status and trigger pipeline
        await self.update_document_status(doc_id, "PROCESSING")
        asyncio.create_task(
            self.process_document_pipeline(doc_id, doc["storage_path"], doc["name"])
        )
        return True

document_service = DocumentService()
