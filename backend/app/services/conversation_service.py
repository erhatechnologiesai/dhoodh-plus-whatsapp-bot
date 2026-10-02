import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional

from app.database.supabase_client import db_service, in_memory_db
from app.whatsapp.client import whatsapp_client
from app.services.redis_service import redis_service
from app.core.logging import logger

class ConversationService:
    """
    Manages conversations, manual admin messages, customer directories,
    and agent assignment.
    """

    async def invalidate_cache(self):
        try:
            await redis_service.delete("cache:conversations:all")
            await redis_service.delete("cache:conversations:ACTIVE")
            await redis_service.delete("cache:conversations:HUMAN_HANDOFF")
            await redis_service.delete("cache:conversations:CLOSED")
            await redis_service.delete("cache:analytics:summary")
        except Exception:
            pass

    async def list_conversations(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        cache_key = f"cache:conversations:{status or 'all'}"
        cached = await redis_service.get_json(cache_key)
        if cached is not None:
            return cached

        client = db_service.get_client()
        conversations: List[Dict[str, Any]] = []

        if db_service.is_connected and client:
            try:
                q = client.table("conversations").select("*, customers(name, whatsapp_number, email)").order("updated_at", desc=True)
                if status:
                    q = q.eq("status", status)
                res = q.execute()
                for c in (res.data or []):
                    cust = c.get("customers") or {}
                    c["customer_name"] = cust.get("name")
                    c["customer_phone"] = cust.get("whatsapp_number")
                    conversations.append(c)
                await redis_service.set_json(cache_key, conversations, expire=6)
                return conversations
            except Exception as e:
                logger.error(f"Error listing conversations from Supabase: {e}")

        # In-memory listing
        for c in in_memory_db.conversations.values():
            if status and c.get("status") != status:
                continue
            cust_id = str(c.get("customer_id"))
            cust = in_memory_db.customers.get(cust_id, {})
            c_copy = dict(c)
            c_copy["customer_name"] = cust.get("name", "Unknown Customer")
            c_copy["customer_phone"] = cust.get("whatsapp_number", "")
            
            # Find latest message
            conv_msgs = [m for m in in_memory_db.messages.values() if str(m.get("conversation_id")) == str(c["id"])]
            conv_msgs.sort(key=lambda x: x.get("created_at", ""))
            if conv_msgs:
                c_copy["last_message"] = conv_msgs[-1]["content"]
                c_copy["last_message_at"] = conv_msgs[-1]["created_at"]
            
            conversations.append(c_copy)

        conversations.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
        return conversations

    async def get_conversation_messages(self, conversation_id: str) -> List[Dict[str, Any]]:
        client = db_service.get_client()
        if db_service.is_connected and client:
            try:
                res = client.table("messages").select("*").eq("conversation_id", conversation_id).order("created_at", desc=False).execute()
                return res.data or []
            except Exception as e:
                logger.error(f"Error fetching conversation messages: {e}")

        msgs = [m for m in in_memory_db.messages.values() if str(m.get("conversation_id")) == str(conversation_id)]
        msgs.sort(key=lambda x: x.get("created_at", ""))
        return msgs

    async def send_agent_message(self, conversation_id: str, content: str, role: str = "HUMAN") -> Dict[str, Any]:
        """
        Human agent sends a message from Admin Dashboard.
        Stores message and delivers to customer's WhatsApp via Cloud API.
        """
        # 1. Lookup customer phone
        phone = None
        conv = in_memory_db.conversations.get(conversation_id)
        if conv:
            cust = in_memory_db.customers.get(str(conv.get("customer_id")))
            if cust:
                phone = cust.get("whatsapp_number")

        client = db_service.get_client()
        if not phone and db_service.is_connected and client:
            try:
                res = client.table("conversations").select("customer_id, customers(whatsapp_number)").eq("id", conversation_id).execute()
                if res.data:
                    phone = res.data[0].get("customers", {}).get("whatsapp_number")
            except Exception as e:
                logger.error(f"Error looking up phone for conversation: {e}")

        # 2. Store message
        msg_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        msg_entry = {
            "id": msg_id,
            "conversation_id": conversation_id,
            "role": role,
            "content": content,
            "message_type": "text",
            "whatsapp_message_id": f"agent_{msg_id[:8]}",
            "metadata": {"sent_by": "human_agent"},
            "created_at": now
        }

        if db_service.is_connected and client:
            try:
                client.table("messages").insert(msg_entry).execute()
                client.table("conversations").update({"updated_at": now}).eq("id", conversation_id).execute()
            except Exception as e:
                logger.error(f"Error saving agent message: {e}")

        in_memory_db.messages[msg_id] = msg_entry
        if conversation_id in in_memory_db.conversations:
            in_memory_db.conversations[conversation_id]["updated_at"] = now

        # 3. Deliver via WhatsApp
        wa_result = {}
        if phone:
            wa_result = await whatsapp_client.send_text_message(phone, content)

        return {
            "message": msg_entry,
            "whatsapp_result": wa_result
        }

    async def update_conversation(
        self,
        conversation_id: str,
        status: Optional[str] = None,
        ai_enabled: Optional[bool] = None,
        assigned_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        update_data = {"updated_at": datetime.utcnow().isoformat()}
        if status:
            update_data["status"] = status
        if ai_enabled is not None:
            update_data["ai_enabled"] = ai_enabled
        if assigned_agent is not None:
            update_data["assigned_agent"] = assigned_agent

        client = db_service.get_client()
        if db_service.is_connected and client:
            try:
                res = client.table("conversations").update(update_data).eq("id", conversation_id).execute()
                if res.data:
                    return res.data[0]
            except Exception as e:
                logger.error(f"Error updating conversation in Supabase: {e}")

        if conversation_id in in_memory_db.conversations:
            in_memory_db.conversations[conversation_id].update(update_data)
            return in_memory_db.conversations[conversation_id]

        return {"id": conversation_id, **update_data}

    async def list_customers(self) -> List[Dict[str, Any]]:
        client = db_service.get_client()
        if db_service.is_connected and client:
            try:
                res = client.table("customers").select("*").order("created_at", desc=True).execute()
                return res.data or []
            except Exception as e:
                logger.error(f"Error listing customers from Supabase: {e}")

        custs = list(in_memory_db.customers.values())
        custs.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return custs

conversation_service = ConversationService()
