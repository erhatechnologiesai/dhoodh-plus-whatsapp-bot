import pytest
import os
import uuid
from uuid import uuid4
from app.rag.extractor import PDFExtractor
from app.rag.chunker import IntelligentChunker
from app.rag.query_rewriter import QueryRewriter
from app.services.rag_service import rag_service
from app.services.ai_service import ai_service
from app.services.document_service import document_service
from app.services.whatsapp_service import whatsapp_service
from app.database.supabase_client import in_memory_db

candidate_paths = [
    os.path.abspath("backend/storage/documents/Dhoodh_Plus_Official_Knowledge_Base.pdf"),
    os.path.abspath("storage/documents/Dhoodh_Plus_Official_Knowledge_Base.pdf"),
    "/app/storage/documents/Dhoodh_Plus_Official_Knowledge_Base.pdf",
    "/app/backend/storage/documents/Dhoodh_Plus_Official_Knowledge_Base.pdf",
]
SAMPLE_PDF_PATH = next((p for p in candidate_paths if os.path.exists(p)), candidate_paths[0])

@pytest.fixture(scope="module")
def sample_pdf():
    assert os.path.exists(SAMPLE_PDF_PATH), f"Sample PDF not found at {SAMPLE_PDF_PATH}"
    return SAMPLE_PDF_PATH

def test_pdf_extraction(sample_pdf):
    data = PDFExtractor.extract_document(sample_pdf)
    assert data["total_pages"] >= 1
    assert "sections" in data
    assert len(data["pages"]) >= 1
    assert sum(p["char_count"] for p in data["pages"]) > 50

def test_intelligent_chunking(sample_pdf):
    data = PDFExtractor.extract_document(sample_pdf)
    chunker = IntelligentChunker(target_chunk_size=500, chunk_overlap=80)
    doc_id = uuid4()
    chunks = chunker.chunk_extracted_data(doc_id, data, doc_name="Dhoodh Plus KB")
    
    assert len(chunks) > 0
    for c in chunks:
        assert c.document_id == doc_id
        assert c.page_number >= 1
        assert c.chunk_index >= 0
        assert len(c.content) > 10

def test_query_rewriter_multilingual():
    # 1. English query
    r1 = QueryRewriter.rewrite_query_with_context("What are the benefits?")
    assert r1["detected_language"] in ["English", "Urdu", "Roman Urdu"]
    assert "benefit" in r1["search_query"].lower() or "doodh" in r1["search_query"].lower()

    # 2. Roman Urdu query
    r2 = QueryRewriter.rewrite_query_with_context("Doodh plus k faiday kia hain?")
    assert "faiday" in r2["search_query"].lower() or "benefits" in r2["search_query"].lower()

    # 3. Short price query in Roman Urdu
    r3 = QueryRewriter.rewrite_query_with_context("iska rate kya ha?")
    assert any(term in r3["search_query"].lower() for term in ["price", "rate", "cost", "doodh"])

    # 4. Pure Urdu script query
    r4 = QueryRewriter.rewrite_query_with_context("قیمت کتنی ہے")
    assert r4["detected_language"] == "Urdu"

def test_grounded_answer_and_pure_urdu_script():
    import asyncio

    async def run_checks():
        # 1. Benefits query in Roman Urdu
        res1 = await ai_service.generate_support_response("doodh plus k faiday kia hain")
        reply1 = res1["response"]
        assert "doodh" in reply1.lower() or "دودھ" in reply1
        assert res1["human_handoff"] is False
        assert len(reply1.splitlines()) <= 4

        # 1b. Benefits query in Pure Urdu Script
        res1_ur = await ai_service.generate_support_response("دودھ پلس کے کیا فائدے ہیں")
        reply1_ur = res1_ur["response"]
        assert "دودھ" in reply1_ur or "فیٹ" in reply1_ur

        # 2. Price query
        res2 = await ai_service.generate_support_response("price kitni hai")
        reply2 = res2["response"]
        assert "1,750" in reply2 or "12,500" in reply2
        assert "delivery" in reply2.lower() or "ڈیلیوری" in reply2

        # 3. Dosage query
        res3 = await ai_service.generate_support_response("bhens ko kitna khilana hai")
        reply3 = res3["response"]
        assert "100" in reply3

        # 4. Out of domain query (Rule 19)
        res_fake = await ai_service.generate_support_response("Kya aap mars par rocket deliver kartay hain?")
        reply_fake = res_fake["response"]
        assert "allah ho traders" in reply_fake.lower() or "doodh plus" in reply_fake.lower() or "اللہ ہو ٹریڈرز" in reply_fake

        # 5. Identity query (Must never say bot or AI)
        res_id = await ai_service.generate_support_response("kya aap bot ho")
        reply_id = res_id["response"].lower()
        assert "main ek bot hoon" not in reply_id
        assert "ai assistant" not in reply_id
        assert "allah ho traders" in reply_id

    asyncio.run(run_checks())

def test_human_handoff_detection():
    # User asks for human agent in Roman Urdu
    is_handoff, reason = ai_service.detect_human_handoff("Mujhe human agent se baat karni hai")
    assert is_handoff is True
    assert "agent" in reason or "human" in reason

    # User asks for human support in Urdu script
    is_handoff2, reason2 = ai_service.detect_human_handoff("مجھے کسی نمائندے سے بات کرنی ہے")
    assert is_handoff2 is True

    # Regular product question should NOT trigger handoff
    is_handoff3, _ = ai_service.detect_human_handoff("doodh plus ki price bata dein")
    assert is_handoff3 is False

@pytest.mark.asyncio
async def test_whatsapp_webhook_flow():
    # Test webhook verification
    challenge = whatsapp_service.verify_webhook(
        mode="subscribe",
        token="dhood_plus_secure_verify_token_2026",
        challenge="CHALLENGE_CODE_123"
    )
    assert challenge == "CHALLENGE_CODE_123"

    # Test incoming message processing with fresh random UUID
    random_msg_id = f"wamid.test.{uuid.uuid4().hex}"
    res = await whatsapp_service.process_incoming_message(
        from_phone="923009998877",
        message_body="doodh plus kitnay ka hai",
        whatsapp_message_id=random_msg_id,
        sender_name="Test Customer"
    )
    assert res["status"] == "responded"
    assert "response" in res
    assert "1,750" in res["response"] or "روپے" in res["response"]
