import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from supabase import create_client

url = 'https://vrblfklcrvlmijfrrinp.supabase.co'
key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZyYmxma2xjcnZsbWlqZnJyaW5wIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc5MDY2NDM2MSwiZXhwIjoyMTA2MjQwMzYxfQ.C1adSPAdt-ZPhdwCAYMycoWqPVXS82McCq9Mwrsreoo'

client = create_client(url, key)
res = client.table('messages').select('*').order('created_at', desc=True).limit(15).execute()
for m in res.data:
    txt = m.get('content', '')[:120].encode('ascii', errors='backslashreplace').decode('ascii')
    print(f"[{m.get('created_at')}] {m.get('role')} (id: {m.get('whatsapp_message_id')}): {txt}")

print("\n--- CONVERSATION 108a7ab2-39f1-4e0c-b034-ae17fc6e745e MESSAGES ---")
conv_msgs = client.table('messages').select('*').eq('conversation_id', '108a7ab2-39f1-4e0c-b034-ae17fc6e745e').order('created_at').execute()
for m in conv_msgs.data:
    txt = m.get('content', '')[:150].encode('ascii', errors='backslashreplace').decode('ascii')
    print(f"[{m.get('created_at')}] {m.get('role')} (id: {m.get('whatsapp_message_id')}): {txt}")
