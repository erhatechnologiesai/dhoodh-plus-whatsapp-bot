import asyncio
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status, BackgroundTasks
from typing import List, Optional
from app.services.document_service import document_service
from app.schemas.document import DocumentResponse, DocumentChunkResponse
from app.core.logging import logger

router = APIRouter(prefix="/documents", tags=["Documents"])

@router.get("", response_model=List[DocumentResponse])
async def list_documents():
    """
    List all uploaded knowledge base documents.
    """
    return await document_service.list_documents()

@router.post("/upload")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    name: Optional[str] = Form(None)
):
    """
    Upload a PDF document.
    Saves file, computes hash, creates record, and triggers background ingestion.
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported."
        )

    content = await file.read()
    file_size = len(content)

    if file_size > 50 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds 50MB limit."
        )

    file_hash = document_service.calculate_file_hash(content)
    doc_name = name or file.filename.replace(".pdf", "").replace("_", " ").title()

    # Save to disk
    storage_path = await document_service.save_uploaded_file(file.filename, content)

    # Create document record with PROCESSING status
    doc_record = await document_service.create_document_record(
        name=doc_name,
        filename=file.filename,
        storage_path=storage_path,
        file_hash=file_hash,
        file_size=file_size
    )

    # Launch ingestion pipeline in background so API responds immediately
    background_tasks.add_task(
        document_service.process_document_pipeline,
        doc_record["id"],
        storage_path,
        doc_name
    )

    return {
        "message": "Document uploaded and processing started in background.",
        "document": doc_record
    }

@router.get("/{doc_id}", response_model=DocumentResponse)
async def get_document(doc_id: str):
    """
    Retrieve document status and metadata.
    """
    doc = await document_service.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc

@router.get("/{doc_id}/chunks", response_model=List[DocumentChunkResponse])
async def get_document_chunks(doc_id: str):
    """
    Inspect the extracted semantic chunks and section titles of a document.
    """
    return await document_service.get_document_chunks(doc_id)

@router.post("/{doc_id}/reindex")
async def reindex_document(doc_id: str):
    """
    Re-index an existing document (re-chunks and regenerates embeddings).
    """
    success = await document_service.reindex_document(doc_id)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found or cannot be re-indexed")
    return {"message": "Re-indexing initiated successfully."}

@router.delete("/{doc_id}")
async def delete_document(doc_id: str):
    """
    Deletes a document and cascades deletion of all its chunks and vector embeddings.
    """
    success = await document_service.delete_document(doc_id)
    return {"message": "Document and associated vector chunks deleted successfully."}
