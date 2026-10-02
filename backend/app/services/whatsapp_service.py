import uuid
import asyncio
from datetime import datetime
from typing import Optional, Dict, Any, List

from app.core.config import settings
from app.core.logging import logger
from app.whatsapp.client import whatsapp_client
from app.services.ai_service import ai_service
from app.services.redis_service import redis_service
from app.database.supabase_client import db_service, in_memory_db

class WhatsAppService:
    """
    Coordinates incoming WhatsApp webhooks, idempotency checking,
    customer resolution, conversational state, RAG-grounded AI agent execution,
    and human handoff workflows.
    """

    def __init__(self):
        self.processed_message_ids = set()

    def verify_webhook(self, mode: Optional[str], token: Optional[str], challenge: Optional[str]) -> Optional[str]:
        """
        Validates Meta's webhook verification challenge.
        """
        if mode == "subscribe" and token == settings.WHATSAPP_VERIFY_TOKEN:
            logger.info("WhatsApp webhook verified successfully!")
            return challenge
        logger.warning(f"WhatsApp webhook verification failed. Received token: {token}")
        return None

    async def get_or_create_customer(self, phone: str, name: Optional[str] = None) -> Dict[str, Any]:
        phone_clean = "".join(filter(str.isdigit, phone))
        client = db_service.get_client()

        if db_service.is_connected and client:
            try:
                res = client.table("customers").select("*").eq("whatsapp_number", phone_clean).execute()
                if res.data:
                    return res.data[0]
                
                # Create customer
                new_customer = {
                    "id": str(uuid.uuid4()),
                    "whatsapp_number": phone_clean,
                    "name": name or f"Customer +{phone_clean}",
                    "email": None,
                    "metadata": {},
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat()
                }
                res_insert = client.table("customers").insert(new_customer).execute()
                if res_insert.data:
                    return res_insert.data[0]
            except Exception as e:
                logger.error(f"Error querying/creating customer in Supabase: {e}")

        # In-memory customer resolution
        for c in in_memory_db.customers.values():
            if c.get("whatsapp_number") == phone_clean:
                return c

        cust_id = str(uuid.uuid4())
        customer = {
            "id": cust_id,
            "whatsapp_number": phone_clean,
            "name": name or f"Customer +{phone_clean}",
            "email": None,
            "metadata": {},
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        in_memory_db.customers[cust_id] = customer
        return customer

    async def get_or_create_active_conversation(self, customer_id: str) -> Dict[str, Any]:
        client = db_service.get_client()
        if db_service.is_connected and client:
            try:
                res = client.table("conversations").select("*").eq("customer_id", customer_id).neq("status", "CLOSED").order("created_at", desc=True).limit(1).execute()
                if res.data:
                    return res.data[0]

                new_conv = {
                    "id": str(uuid.uuid4()),
                    "customer_id": customer_id,
                    "status": "ACTIVE",
                    "assigned_agent": None,
                    "ai_enabled": True,
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat()
                }
                res_insert = client.table("conversations").insert(new_conv).execute()
                if res_insert.data:
                    return res_insert.data[0]
            except Exception as e:
                logger.error(f"Error in Supabase conversation lookup: {e}")

        # In-memory lookup
        for conv in in_memory_db.conversations.values():
            if str(conv.get("customer_id")) == str(customer_id) and conv.get("status") != "CLOSED":
                return conv

        conv_id = str(uuid.uuid4())
        conversation = {
            "id": conv_id,
            "customer_id": customer_id,
            "status": "ACTIVE",
            "assigned_agent": None,
            "ai_enabled": True,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        in_memory_db.conversations[conv_id] = conversation
        return conversation

    async def save_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        whatsapp_message_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        msg_id = str(uuid.uuid4())
        msg_data = {
            "id": msg_id,
            "conversation_id": conversation_id,
            "role": role,
            "content": content,
            "message_type": "text",
            "whatsapp_message_id": whatsapp_message_id,
            "metadata": metadata or {},
            "created_at": datetime.utcnow().isoformat()
        }

        client = db_service.get_client()
        if db_service.is_connected and client:
            try:
                res = client.table("messages").insert(msg_data).execute()
                if res.data:
                    return res.data[0]
            except Exception as e:
                logger.error(f"Error saving message to Supabase: {e}")

        in_memory_db.messages[msg_id] = msg_data
        return msg_data

    async def get_recent_messages(self, conversation_id: str, limit: int = 6) -> List[Dict[str, str]]:
        client = db_service.get_client()
        if db_service.is_connected and client:
            try:
                res = client.table("messages").select("role, content").eq("conversation_id", conversation_id).order("created_at", desc=True).limit(limit).execute()
                if res.data:
                    msgs = list(reversed(res.data))
                    return [{"role": "assistant" if m["role"] in ["ASSISTANT", "HUMAN"] else "user", "content": m["content"]} for m in msgs]
            except Exception as e:
                logger.error(f"Error fetching recent messages: {e}")

        all_msgs = [m for m in in_memory_db.messages.values() if str(m.get("conversation_id")) == str(conversation_id)]
        all_msgs.sort(key=lambda x: x.get("created_at", ""))
        recent = all_msgs[-limit:] if len(all_msgs) > limit else all_msgs
        return [{"role": "assistant" if m["role"] in ["ASSISTANT", "HUMAN"] else "user", "content": m["content"]} for m in recent]

    async def record_ai_log(
        self,
        conversation_id: str,
        query: str,
        retrieved_chunks: List[Dict[str, Any]],
        similarity_scores: List[float],
        generated_response: str,
        model: str,
        latency_ms: float,
        token_usage: Dict[str, Any]
    ):
        log_id = str(uuid.uuid4())
        log_entry = {
            "id": log_id,
            "conversation_id": conversation_id,
            "query": query,
            "retrieved_chunks": retrieved_chunks,
            "similarity_scores": similarity_scores,
            "generated_response": generated_response,
            "model": model,
            "latency": latency_ms,
            "token_usage": token_usage,
            "created_at": datetime.utcnow().isoformat()
        }

        client = db_service.get_client()
        if db_service.is_connected and client:
            try:
                client.table("ai_logs").insert(log_entry).execute()
            except Exception as e:
                logger.error(f"Error saving AI log to Supabase: {e}")

        in_memory_db.ai_logs[log_id] = log_entry

    async def trigger_human_handoff(self, conversation_id: str, reason: str):
        # Update conversation status
        client = db_service.get_client()
        now = datetime.utcnow().isoformat()
        if db_service.is_connected and client:
            try:
                client.table("conversations").update({
                    "status": "HUMAN_HANDOFF",
                    "ai_enabled": False,
                    "updated_at": now
                }).eq("id", conversation_id).execute()

                handoff_entry = {
                    "id": str(uuid.uuid4()),
                    "conversation_id": conversation_id,
                    "reason": reason,
                    "assigned_to": None,
                    "status": "PENDING",
                    "created_at": now
                }
                client.table("human_handoffs").insert(handoff_entry).execute()
            except Exception as e:
                logger.error(f"Error creating human handoff in Supabase: {e}")

        if conversation_id in in_memory_db.conversations:
            in_memory_db.conversations[conversation_id].update({
                "status": "HUMAN_HANDOFF",
                "ai_enabled": False,
                "updated_at": now
            })
        
        handoff_id = str(uuid.uuid4())
        in_memory_db.human_handoffs[handoff_id] = {
            "id": handoff_id,
            "conversation_id": conversation_id,
            "reason": reason,
            "assigned_to": None,
            "status": "PENDING",
            "created_at": now
        }
        logger.info(f"Human handoff initiated for conversation {conversation_id}: {reason}")

    async def process_incoming_message(
        self,
        from_phone: str,
        message_body: str,
        whatsapp_message_id: str,
        sender_name: Optional[str] = None,
        is_voice: bool = False,
        skip_outbound: bool = False
    ) -> Dict[str, Any]:
        """
        Complete message handling pipeline:
        Idempotency -> Customer -> Conversation -> Memory -> AI / Handoff -> Outbound WhatsApp
        """
        # Idempotency check with Redis (distributed & persisted)
        is_duplicate = await redis_service.check_and_set_idempotency(whatsapp_message_id)
        if is_duplicate or whatsapp_message_id in self.processed_message_ids:
            logger.info(f"Duplicate message ignored: {whatsapp_message_id}")
            return {"status": "duplicate_ignored"}

        self.processed_message_ids.add(whatsapp_message_id)

        # Mark message read on WhatsApp
        asyncio.create_task(whatsapp_client.mark_message_as_read(whatsapp_message_id))

        # 1. Resolve Customer & Conversation
        customer = await self.get_or_create_customer(from_phone, sender_name)
        conversation = await self.get_or_create_active_conversation(customer["id"])
        conversation_id = conversation["id"]

        # 2. Save Incoming Message
        await self.save_message(
            conversation_id=conversation_id,
            role="USER",
            content=message_body,
            whatsapp_message_id=whatsapp_message_id
        )

        # 3. Check Conversation State & Master Bot Switch
        master_bot_enabled = bool(in_memory_db.system_settings.get("bot_enabled", True))

        if not master_bot_enabled:
            logger.info(f"[MANUAL MODE] Master AI Bot is OFF. Conversation {conversation_id} message saved for human agent.")
            return {
                "status": "awaiting_human_agent",
                "conversation_id": conversation_id,
                "customer_id": customer["id"],
                "reason": "master_bot_off"
            }

        is_human_handoff = conversation.get("status") == "HUMAN_HANDOFF"
        is_ai_enabled = conversation.get("ai_enabled", True)

        if is_human_handoff or not is_ai_enabled:
            logger.info(f"Conversation {conversation_id} is in HUMAN_HANDOFF or AI disabled. Skipping auto AI response.")
            return {
                "status": "awaiting_human_agent",
                "conversation_id": conversation_id,
                "customer_id": customer["id"]
            }

        # 4. Fetch recent conversation memory for co-reference and context
        recent_history = await self.get_recent_messages(conversation_id, limit=settings.MAX_HISTORY_MESSAGES)

        # 5. Execute AI Customer Support Agent with RAG
        ai_result = await ai_service.generate_support_response(
            query=message_body,
            conversation_history=recent_history,
            is_voice=is_voice
        )

        response_text = ai_result["response"]

        # 6. Check if AI detected need for Human Handoff
        if ai_result["human_handoff"]:
            await self.trigger_human_handoff(
                conversation_id=conversation_id,
                reason=ai_result["handoff_reason"] or "User requested human representative"
            )

        # 7. Save Assistant Message
        await self.save_message(
            conversation_id=conversation_id,
            role="ASSISTANT",
            content=response_text,
            metadata={
                "model": ai_result["model"],
                "latency_ms": ai_result["latency_ms"],
                "rag_relevant": ai_result["rag_result"]["is_relevant"]
            }
        )

        # 8. Send WhatsApp Response
        wa_response = None
        if not skip_outbound:
            wa_response = await whatsapp_client.send_text_message(from_phone, response_text)

        # 9. Record Observability AI Log
        asyncio.create_task(
            self.record_ai_log(
                conversation_id=conversation_id,
                query=message_body,
                retrieved_chunks=ai_result["rag_result"]["chunks"],
                similarity_scores=ai_result["rag_result"]["similarity_scores"],
                generated_response=response_text,
                model=ai_result["model"],
                latency_ms=ai_result["latency_ms"],
                token_usage=ai_result["token_usage"]
            )
        )

        return {
            "status": "responded",
            "conversation_id": conversation_id,
            "response": response_text,
            "whatsapp_response": wa_response
        }

whatsapp_service = WhatsAppService()
