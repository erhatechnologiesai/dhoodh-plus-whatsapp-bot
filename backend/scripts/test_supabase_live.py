import os
import sys

# Ensure backend root is in python path
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_root = os.path.dirname(current_dir)
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

from supabase import create_client

SUPABASE_URL = "https://vrblfklcrvlmijfrrinp.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZyYmxma2xjcnZsbWlqZnJyaW5wIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc5MDY2NDM2MSwiZXhwIjoyMTA2MjQwMzYxfQ.C1adSPAdt-ZPhdwCAYMycoWqPVXS82McCq9Mwrsreoo"

def main():
    print(f"Connecting to Supabase at: {SUPABASE_URL} ...")
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # 1. Test system_settings table
    print("Checking 'system_settings' table...")
    res = client.table("system_settings").select("*").execute()
    print(f"system_settings rows: {len(res.data)}")
    
    # 2. Test documents table
    print("Checking 'documents' table...")
    res_docs = client.table("documents").select("id, name, status").execute()
    print(f"documents rows: {len(res_docs.data)}")
    
    # 3. Test customers table
    print("Checking 'customers' table...")
    res_cust = client.table("customers").select("*").execute()
    print(f"customers rows: {len(res_cust.data)}")

    print("\nSUCCESS! Your live Supabase database is 100% connected and responding properly!")

if __name__ == "__main__":
    main()
