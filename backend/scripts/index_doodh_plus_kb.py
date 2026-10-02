import sys
import os
import asyncio

# Ensure backend root is in python path
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_root = os.path.dirname(current_dir)
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

from scripts.generate_sample_pdf import generate_official_doodh_plus_pdf
from app.services.document_service import document_service
from app.services.ai_service import ai_service
from app.rag.extractor import PDFExtractor
from app.core.logging import logger

PDF_PATH = os.path.join(backend_root, "storage", "documents", "Dhoodh_Plus_Official_Knowledge_Base.pdf")

async def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    print("1. Generating official PDF from user knowledge base...")
    generate_official_doodh_plus_pdf(PDF_PATH)

    print("2. Reading and extracting knowledge...")
    with open(PDF_PATH, "rb") as f:
        content = f.read()

    file_hash = document_service.calculate_file_hash(content)
    doc_record = await document_service.create_document_record(
        name="Doodh Plus Official Handbook (Allah Ho Traders)",
        filename="Dhoodh_Plus_Official_Knowledge_Base.pdf",
        storage_path=PDF_PATH,
        file_hash=file_hash,
        file_size=len(content)
    )

    doc_id = doc_record["id"]
    print(f"3. Indexing document {doc_id} into pgvector knowledge base...")
    await document_service.process_document_pipeline(
        doc_id=doc_id,
        file_path=PDF_PATH,
        doc_name="Doodh Plus Official Handbook (Allah Ho Traders)"
    )

    print("4. Document status: READY! Testing grounded query answers...\n")

    # Test questions from the PDF
    test_queries = [
        "Doodh Plus ki price kya hai?",
        "Gaye aur bhains ko kitni khorak deni hai?",
        "Kya yeh hamla janwar ke liye safe hai?",
        "Mera janwar mitti aur deewar chaat raha hai, kya karoon?",
        "Delivery ke kitne charges hain?",
        "Order kaise book karwayen?",
        "Kya aap rocket deliver karte ho?" # Strict anti-hallucination test
    ]

    for q in test_queries:
        print(f"--------------------------------------------------")
        print(f"Customer: {q}")
        res = await ai_service.generate_support_response(q)
        print(f"AI Bot: {res['response']}")

if __name__ == "__main__":
    asyncio.run(main())
