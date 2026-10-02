import os
import sys
from supabase import create_client

url = 'https://vrblfklcrvlmijfrrinp.supabase.co'
key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZyYmxma2xjcnZsbWlqZnJyaW5wIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc5MDY2NDM2MSwiZXhwIjoyMTA2MjQwMzYxfQ.C1adSPAdt-ZPhdwCAYMycoWqPVXS82McCq9Mwrsreoo'
c = create_client(url, key)

sys.stdout.reconfigure(encoding='utf-8')

res = c.table('messages').select('*').eq('conversation_id', '108a7ab2-39f1-4e0c-b034-ae17fc6e745e').order('created_at', desc=False).execute()

output_lines = [f"Total messages: {len(res.data)}", "=" * 80]
for m in res.data[-20:]:
    role = m.get('role')
    msg_id = m.get('whatsapp_message_id')
    created_at = m.get('created_at')
    content = m.get('content', '')
    output_lines.append(f"[{created_at}] [{role}] ({msg_id}):\n   {content}\n" + "-" * 80)

full_output = "\n".join(output_lines)
with open('backend/scripts/recent_conv_log.txt', 'w', encoding='utf-8') as fh:
    fh.write(full_output)

print("Saved to backend/scripts/recent_conv_log.txt successfully.")
