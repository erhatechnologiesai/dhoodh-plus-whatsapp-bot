import asyncio
import os
import sys

# Ensure backend root is in python path
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_root = os.path.dirname(current_dir)
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

from app.services.document_service import document_service
from app.database.supabase_client import db_service

PDF_PATH = os.path.join(backend_root, "storage", "documents", "Dhoodh_Plus_Official_Knowledge_Base.pdf")

async def main():
    print("Ingesting Doodh Plus PDF into your LIVE Supabase Database...")
    print(f"Is Supabase connected in db_service? {db_service.is_connected}")
    
    with open(PDF_PATH, "rb") as f:
        content = f.read()

    file_hash = document_service.calculate_file_hash(content)
    
    # 1. Create document record in Supabase
    doc_record = await document_service.create_document_record(
        name="Doodh Plus Official Handbook (Allah Ho Traders)",
        filename="Dhoodh_Plus_Official_Knowledge_Base.pdf",
        storage_path=PDF_PATH,
        file_hash=file_hash,
        file_size=len(content)
    )
    doc_id = doc_record["id"]
    print(f"Document created in Supabase with ID: {doc_id}")

    # 2. Extract, chunk, embed and store into document_chunks table in Supabase
    await document_service.process_document_pipeline(
        doc_id=doc_id,
        file_path=PDF_PATH,
        doc_name="Doodh Plus Official Handbook (Allah Ho Traders)"
    )

    # 3. Verify chunks stored in Supabase
    client = db_service.get_client()
    res_chunks = client.table("document_chunks").select("id, section_title, page_number").eq("document_id", doc_id).execute()
    print(f"Total chunks stored in Supabase document_chunks: {len(res_chunks.data)}")
    print("SUCCESS: Your live Supabase database now holds the full vector knowledge base!")

if __name__ == "__main__":
    asyncio.run(main())
