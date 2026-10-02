import pytest
import os
import asyncio
from uuid import uuid4
from app.rag.extractor import PDFExtractor
from app.rag.chunker import IntelligentChunker
from app.rag.query_rewriter import QueryRewriter
from app.embeddings.provider import get_embedding_provider
from app.services.rag_service import rag_service
from app.services.ai_service import ai_service
from app.services.document_service import document_service
from app.services.whatsapp_service import whatsapp_service
from app.database.supabase_client import in_memory_db

SAMPLE_PDF_PATH = "c:/Users/surface/OneDrive/Desktop/DHOOD PLUS WATSAPP CHATBOT/backend/storage/documents/Dhoodh_Plus_Official_Knowledge_Base.pdf"

@pytest.fixture(scope="module")
def sample_pdf():
    assert os.path.exists(SAMPLE_PDF_PATH), f"Sample PDF not found at {SAMPLE_PDF_PATH}"
    return SAMPLE_PDF_PATH

def test_pdf_extraction(sample_pdf):
    data = PDFExtractor.extract_document(sample_pdf)
    assert data["total_pages"] >= 2
    assert len(data["sections"]) >= 4
    # Check that key sections were recognized
    section_titles = [s["title"].upper() for s in data["sections"]]
    assert any("PRODUCT" in t or "SPECIFICATIONS" in t for t in section_titles)
    assert any("WARRANTY" in t for t in section_titles)
    assert any("TROUBLESHOOTING" in t for t in section_titles)

def test_intelligent_chunking(sample_pdf):
    data = PDFExtractor.extract_document(sample_pdf)
    chunker = IntelligentChunker(target_chunk_size=500, chunk_overlap=80)
    doc_id = uuid4()
    chunks = chunker.chunk_extracted_data(doc_id, data, doc_name="Dhoodh Plus KB")
    
    assert len(chunks) > 0
    # Every chunk must have document_id, page_number, chunk_index, and section_title
    for c in chunks:
        assert c.document_id == doc_id
        assert c.page_number >= 1
        assert c.chunk_index >= 0
        assert len(c.content) > 15
        assert c.section_title is not None

def test_query_rewriter_multilingual():
    # 1. English
    r1 = QueryRewriter.rewrite_query_with_context("What is the warranty?")
    assert r1["detected_language"] == "English"

    # 2. Roman Urdu
    r2 = QueryRewriter.rewrite_query_with_context("Product A ki warranty kitni ha?")
    assert r2["detected_language"] == "Roman Urdu"
    assert "warranty" in r2["search_query"].lower()

    # 3. Short price query in Roman Urdu
    r3 = QueryRewriter.rewrite_query_with_context("iska rate kya ha?")
    assert r3["detected_language"] == "Roman Urdu"
    assert any(term in r3["search_query"] for term in ["price", "rate", "cost"])

    # 4. Contextual follow-up co-reference
    history = [
        {"role": "user", "content": "Mujhe Product A ke bare mein information chahiye."},
        {"role": "assistant", "content": "Product A ke kis aspect ke bare mein information chahiye?"}
    ]
    r4 = QueryRewriter.rewrite_query_with_context("Warranty kitni hai?", history)
    assert "Product A" in r4["search_query"]

@pytest.mark.asyncio
async def test_end_to_end_document_ingestion_and_rag(sample_pdf):
    # Ingest document through DocumentService
    with open(sample_pdf, "rb") as f:
        content = f.read()

    file_hash = document_service.calculate_file_hash(content)
    doc_record = await document_service.create_document_record(
        name="Dhoodh Plus Official KB",
        filename="Dhoodh_Plus_Official_Knowledge_Base.pdf",
        storage_path=sample_pdf,
        file_hash=file_hash,
        file_size=len(content)
    )

    doc_id = doc_record["id"]
    await document_service.process_document_pipeline(
        doc_id=doc_id,
        file_path=sample_pdf,
        doc_name="Dhoodh Plus Official KB"
    )

    # Verify document status
    doc = await document_service.get_document(doc_id)
    assert doc["status"] == "READY"
    assert doc["page_count"] >= 2
    assert doc["chunk_count"] > 0

    # Test RAG retrieval for warranty
    rag_res = await rag_service.retrieve_context_for_query("Product A warranty terms", threshold=0.20)
    assert rag_res["is_relevant"] is True
    assert len(rag_res["chunks"]) > 0
    assert "2 Year" in rag_res["context_text"] or "warranty" in rag_res["context_text"].lower()

@pytest.mark.asyncio
async def test_grounded_answer_and_hallucination_control():
    # 1. Known question in Roman Urdu
    res1 = await ai_service.generate_support_response("Product A ki warranty kitni ha?")
    assert "2" in res1["response"] or "saal" in res1["response"].lower() or "year" in res1["response"].lower()
    assert res1["human_handoff"] is False

    # 2. Troubleshooting question (Error E03)
    res2 = await ai_service.generate_support_response("E03 error aa raha hai")
    assert "E03" in res2["response"] or "sensor" in res2["response"].lower()

    # 3. Troubleshooting question (Kaam nahi kar raha)
    res3 = await ai_service.generate_support_response("mera product kaam nahi kar raha")
    assert "help" in res3["response"].lower() or "madad" in res3["response"].lower() or "error" in res3["response"].lower()

    # 4. Completely unsupported question (No hallucination test)
    # Asking for rocket ship delivery to mars
    res_fake = await ai_service.generate_support_response("Kya aap mars par rocket deliver kartay hain?")
    # Must NOT hallucinate that rocket delivery to mars is possible!
    assert ("not available" in res_fake["response"].lower() or 
            "information mojood nahi" in res_fake["response"].lower() or
            "couldn't find" in res_fake["response"].lower() or
            "support representative" in res_fake["response"].lower())

@pytest.mark.asyncio
async def test_human_handoff_detection():
    # User asks for human agent in Roman Urdu
    is_handoff, reason = ai_service.detect_human_handoff("Mujhe human agent se baat karni hai")
    assert is_handoff is True
    assert "agent" in reason or "human" in reason

    # User asks for human support in English
    is_handoff2, reason2 = ai_service.detect_human_handoff("Please connect me with a representative")
    assert is_handoff2 is True

@pytest.mark.asyncio
async def test_whatsapp_webhook_flow():
    # Test webhook verification
    challenge = whatsapp_service.verify_webhook(
        mode="subscribe",
        token="dhood_plus_secure_verify_token_2026",
        challenge="CHALLENGE_CODE_123"
    )
    assert challenge == "CHALLENGE_CODE_123"

    # Test incoming message processing
    res = await whatsapp_service.process_incoming_message(
        from_phone="923009998877",
        message_body="Product A ki warranty kitni hai?",
        whatsapp_message_id="wamid.test.001",
        sender_name="Ahmed Khan"
    )
    assert res["status"] == "responded"
    assert "response" in res
    assert "2" in res["response"] or "saal" in res["response"] or "year" in res["response"].lower()

    # Test idempotency (duplicate message should be ignored)
    res_dup = await whatsapp_service.process_incoming_message(
        from_phone="923009998877",
        message_body="Product A ki warranty kitni hai?",
        whatsapp_message_id="wamid.test.001",
        sender_name="Ahmed Khan"
    )
    assert res_dup["status"] == "duplicate_ignored"

    # Test human handoff transition via message
    res_handoff = await whatsapp_service.process_incoming_message(
        from_phone="923009998877",
        message_body="Main insan se baat karna chahta hoon, agent se connect karo",
        whatsapp_message_id="wamid.test.002",
        sender_name="Ahmed Khan"
    )
    conv_id = res_handoff["conversation_id"]
    conv = in_memory_db.conversations.get(conv_id)
    assert conv["status"] == "HUMAN_HANDOFF"
    assert conv["ai_enabled"] is False
