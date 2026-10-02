from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID

class DocumentStatus(str):
    UPLOADING = "UPLOADING"
    PROCESSING = "PROCESSING"
    READY = "READY"
    FAILED = "FAILED"

class DocumentChunkResponse(BaseModel):
    id: UUID
    document_id: UUID
    content: str
    page_number: int
    chunk_index: int
    section_title: Optional[str] = None
    metadata: Dict[str, Any] = {}
    similarity: Optional[float] = None
    created_at: Optional[datetime] = None

class DocumentResponse(BaseModel):
    id: UUID
    name: str
    original_filename: str
    storage_path: Optional[str] = None
    file_hash: Optional[str] = None
    file_size: int
    page_count: int
    status: str
    processing_error: Optional[str] = None
    chunk_count: Optional[int] = 0
    created_at: datetime
    updated_at: datetime

class DocumentUploadResponse(BaseModel):
    message: str
    document: DocumentResponse
