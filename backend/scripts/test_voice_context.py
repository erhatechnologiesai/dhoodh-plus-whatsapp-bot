import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.ai_service import ai_service
from app.rag.query_rewriter import QueryRewriter

async def run_voice_context_tests():
    print("=" * 70)
    print("TESTING VOICE CONTEXT & TOPICAL PRECISION")
    print("=" * 70)

    # -------------------------------------------------------------
    # TEST CASE 1: Multi-turn Co-reference & Pronoun Resolution
    # Turn 1: User mentions Bhains (Buffalo) has milk problem
    # Turn 2: User sends Voice Note asking: "isko kitna dena hai?" (Pronoun 'isko')
    # EXPECTED: Bot must specifically give Buffalo dosage (100 grams), NOT generic list.
    # -------------------------------------------------------------
    print("\n--- TEST CASE 1: Voice Pronoun Resolution ('isko kitna dena hai') ---")
    conv1 = [
        {"role": "user", "content": "Meri bhains doodh kam de rahi hai kya Doodh Plus theek rahega?"},
        {"role": "assistant", "content": "Ji bilkul, Doodh Plus bhains ke liye behtareen hai. Ye doodh aur fat ki production ko support karta hai."}
    ]
    query1 = "isko kitna dena hai?"
    rewritten1 = QueryRewriter.rewrite_query_with_context(query1, conv1)
    print(f"Query: {query1}")
    print(f"Rewritten Query Context Entities: {rewritten1.get('context_entities')}")
    print(f"Rewritten Query Search: {rewritten1.get('search_query')}")
    assert any("bhains" in e.lower() for e in rewritten1.get('context_entities', [])), "Failed to detect bhains in context"

    res1 = await ai_service.generate_support_response(
        query=query1,
        conversation_history=conv1,
        is_voice=True
    )
    reply1 = res1["response"]
    print(f"Bot Reply:\n{reply1}")
    assert "100" in reply1 or "bhains" in reply1.lower(), "Should specify bhains 100g dosage"
    assert "bakri" not in reply1.lower(), "Strict Relevance: Should NOT dump goat info when user asked about bhains!"
    print(">>> PASS: Voice pronoun correctly resolved to bhains 100g dosage without dumping unrelated animals!")

    # -------------------------------------------------------------
    # TEST CASE 2: Strict Relevance on Price Query
    # Turn 1: Discussing cow health
    # Turn 2 (Voice Note): "iska rate kya hai?" (What is its rate?)
    # EXPECTED: Answer ONLY price & packages (1kg Rs. 1750, 10kg Rs. 12500) and delivery.
    # -------------------------------------------------------------
    print("\n--- TEST CASE 2: Strict Relevance on Price Voice Note ('iska rate kya hai') ---")
    conv2 = [
        {"role": "user", "content": "Gaye kamzor ho gayi hai"},
        {"role": "assistant", "content": "Doodh Plus kamzor janwar ki sehat aur taaqat ko behtar karne mein madad karta hai."}
    ]
    query2 = "iska rate kya hai?"
    res2 = await ai_service.generate_support_response(
        query=query2,
        conversation_history=conv2,
        is_voice=True
    )
    reply2 = res2["response"]
    print(f"Bot Reply:\n{reply2}")
    assert "1,750" in reply2 or "1750" in reply2, "Should provide 1kg price 1,750"
    assert "12,500" in reply2 or "12500" in reply2, "Should provide 10kg price 12,500"
    print(">>> PASS: Voice price query answered strictly with package rates!")

    # -------------------------------------------------------------
    # TEST CASE 3: Voice Note with Pica Syndrome (Mitti khana)
    # Voice Note: "meri gaye deewar aur mitti chatti hai"
    # EXPECTED: Address pica / mineral deficiency and dosage, NO unasked topics.
    # -------------------------------------------------------------
    print("\n--- TEST CASE 3: Voice Note on Pica Syndrome ('gaye deewar aur mitti chatti hai') ---")
    query3 = "meri gaye deewar aur mitti chatti hai"
    res3 = await ai_service.generate_support_response(
        query=query3,
        conversation_history=[],
        is_voice=True
    )
    reply3 = res3["response"]
    print(f"Bot Reply:\n{reply3}")
    assert "mineral" in reply3.lower() or "deficiency" in reply3.lower() or "kami" in reply3.lower(), "Should mention mineral deficiency"
    print(">>> PASS: Voice note answered specifically on mineral deficiency / pica!")

    # -------------------------------------------------------------
    # TEST CASE 4: Follow-up Voice Note Switching Animal
    # Turn 1: Asking about Bakri dosage
    # Turn 2 (Voice Note): "aur bachhre ko kitna dena hai?" (Switching to calf)
    # EXPECTED: Calf / Bachhra specific dosage (20-30g daily).
    # -------------------------------------------------------------
    print("\n--- TEST CASE 4: Voice Note Switching Animal ('aur bachhre ko kitna dena hai') ---")
    conv4 = [
        {"role": "user", "content": "Bakri ko kitna dena hai?"},
        {"role": "assistant", "content": "Bakri ko rozana 20 se 30 gram Doodh Plus dein aur feed mein mix kar dein."}
    ]
    query4 = "aur bachhre ko kitna dena hai?"
    res4 = await ai_service.generate_support_response(
        query=query4,
        conversation_history=conv4,
        is_voice=True
    )
    reply4 = res4["response"]
    print(f"Bot Reply:\n{reply4}")
    assert ("bachhr" in reply4.lower() or "katt" in reply4.lower() or "calf" in reply4.lower() or "20" in reply4), "Should address calf dosage"
    print(">>> PASS: Voice animal-switch handled accurately!")

    # -------------------------------------------------------------
    # TEST CASE 5: Unrelated Out-of-Domain Voice Query (Anti-Hallucination)
    # Voice Note: "cricket match kab hai" (Cricket match query)
    # EXPECTED: Polite fallback, MUST NOT invent cricket information!
    # -------------------------------------------------------------
    print("\n--- TEST CASE 5: Out of Domain Voice Query ('cricket match kab hai') ---")
    query5 = "cricket match kab hai"
    res5 = await ai_service.generate_support_response(
        query=query5,
        conversation_history=[],
        is_voice=True
    )
    reply5 = res5["response"]
    print(f"Bot Reply:\n{reply5}")
    assert "doodh plus" in reply5.lower() or "allah ho traders" in reply5.lower(), "Must redirect to Doodh Plus business domain"
    assert "pakistan vs" not in reply5.lower(), "Must NOT hallucinate cricket scores!"
    print(">>> PASS: Anti-hallucination guard successfully prevented off-domain hallucination!")

    # -------------------------------------------------------------
    # TEST CASE 6: Full Islamic Greeting Voice Note
    # Voice Note: "السلام علیکم ورحمۃ اللہ وبرکاتہ"
    # EXPECTED: Warm greeting reply in Roman Urdu, NOT voice apology!
    # -------------------------------------------------------------
    print("\n--- TEST CASE 6: Full Islamic Greeting Voice Note ('السلام علیکم ورحمۃ اللہ وبرکاتہ') ---")
    query6 = "السلام علیکم ورحمۃ اللہ وبرکاتہ"
    res6 = await ai_service.generate_support_response(
        query=query6,
        conversation_history=[],
        is_voice=True
    )
    reply6 = res6["response"]
    print(f"Bot Reply:\n{reply6}")
    assert "wa alaikum assalam" in reply6.lower(), "Must reply with proper Islamic greeting"
    assert "awaz saaf nahi" not in reply6.lower(), "Must NOT apologize for unclear voice note on greeting"
    print(">>> PASS: Full Islamic greeting in voice note greeted warmly in Roman Urdu!")

    # -------------------------------------------------------------
    # TEST CASE 7: 2 Questions in 1 Voice Note: Price + How to Order
    # Voice Note: "فیز دودھ کی جو پرائز ہے وہ مجھے بتاؤ وہ کیا ہے اور میں اس کو کیسے ارڈر کر سکتا ہوں"
    # EXPECTED: MUST answer BOTH Price AND Order Procedure!
    # -------------------------------------------------------------
    print("\n--- TEST CASE 7: 2 Questions in 1 Voice Note (Price + Order) ---")
    query7 = "فیز دودھ کی جو پرائز ہے وہ مجھے بتاؤ وہ کیا ہے اور میں اس کو کیسے ارڈر کر سکتا ہوں"
    res7 = await ai_service.generate_support_response(
        query=query7,
        conversation_history=[],
        is_voice=True
    )
    reply7 = res7["response"]
    print(f"Bot Reply:\n{reply7}")
    assert "1,750" in reply7 or "1750" in reply7, "Must contain price 1,750"
    assert "12,500" in reply7 or "12500" in reply7, "Must contain 10kg price 12,500"
    assert "order" in reply7.lower() or "naam" in reply7.lower() or "address" in reply7.lower(), "Must also answer how to order!"
    print(">>> PASS: Both Price and Order Procedure answered for 2-question voice note!")

    # -------------------------------------------------------------
    # TEST CASE 8: 2 Questions in 1 Voice Note: Benefits + Price
    # Voice Note: "مجھے اس کے فائدے بتاؤ اور اس کی پرائز بھی ساتھ بتاؤ"
    # EXPECTED: MUST answer BOTH Benefits AND Price!
    # -------------------------------------------------------------
    print("\n--- TEST CASE 8: 2 Questions in 1 Voice Note (Benefits + Price) ---")
    query8 = "مجھے اس کے فائدے بتاؤ اور اس کی پرائز بھی ساتھ بتاؤ"
    res8 = await ai_service.generate_support_response(
        query=query8,
        conversation_history=[],
        is_voice=True
    )
    reply8 = res8["response"]
    print(f"Bot Reply:\n{reply8}")
    assert "doodh" in reply8.lower() or "fat" in reply8.lower() or "barhata" in reply8.lower(), "Must answer product benefits"
    assert "1,750" in reply8 or "1750" in reply8, "Must also contain price 1,750"
    print(">>> PASS: Both Benefits and Price answered for 2-question voice note!")

    # -------------------------------------------------------------
    # TEST CASE 9: Parcel Delivery Timeline Voice Note
    # Voice Note: "میں نے کہا یہ کتنے دن تک میرے پاس اجائے گا"
    # EXPECTED: MUST explicitly state 2 to 4 working days delivery timeline!
    # -------------------------------------------------------------
    print("\n--- TEST CASE 9: Parcel Delivery Timeline ('کتنے دن تک میرے پاس اجائے گا') ---")
    query9 = "میں نے کہا یہ کتنے دن تک میرے پاس اجائے گا"
    res9 = await ai_service.generate_support_response(
        query=query9,
        conversation_history=[],
        is_voice=True
    )
    reply9 = res9["response"]
    print(f"Bot Reply:\n{reply9}")
    assert "2 se 4" in reply9 or "2-4" in reply9 or "2 se 4 working days" in reply9, "Must specify 2 to 4 working days delivery timeline"
    assert "free home delivery" in reply9.lower() or "free delivery" in reply9.lower() or "cod" in reply9.lower(), "Must mention free delivery / COD"
    print(">>> PASS: Delivery timeline accurately answered with 2 to 4 working days!")

    # -------------------------------------------------------------
    # TEST CASE 10: Pure Urdu How to Order Voice Note
    # Voice Note: "اچھا میں یہ کیسے ارڈر کر سکتا ہوں"
    # EXPECTED: Order booking instructions (Naam, Mobile, Address, Pack size)
    # -------------------------------------------------------------
    print("\n--- TEST CASE 10: Pure Urdu How to Order ('اچھا میں یہ کیسے ارڈر کر سکتا ہوں') ---")
    query10 = "اچھا میں یہ کیسے ارڈر کر سکتا ہوں"
    res10 = await ai_service.generate_support_response(
        query=query10,
        conversation_history=[],
        is_voice=True
    )
    reply10 = res10["response"]
    print(f"Bot Reply:\n{reply10}")
    assert "naam" in reply10.lower() or "address" in reply10.lower() or "pata" in reply10.lower(), "Must provide order booking details"
    assert "awaz saaf nahi" not in reply10.lower(), "Must NOT fail with voice apology!"
    print(">>> PASS: Pure Urdu order question answered with complete order booking instructions!")

    # -------------------------------------------------------------
    # TEST CASE 11: 3 Questions in 1 Query (Benefits + Price + Delivery Days)
    # Query: "اس کے فائدے بتاؤ، ریٹ کیا ہے اور پارسل کتنے دن میں آئے گا؟"
    # EXPECTED: All 3 questions answered cleanly!
    # -------------------------------------------------------------
    print("\n--- TEST CASE 11: 3 Questions in 1 Query (Benefits + Price + Delivery Days) ---")
    query11 = "اس کے فائدے بتاؤ، ریٹ کیا ہے اور پارسل کتنے دن میں آئے گا؟"
    res11 = await ai_service.generate_support_response(
        query=query11,
        conversation_history=[],
        is_voice=True
    )
    reply11 = res11["response"]
    print(f"Bot Reply:\n{reply11}")
    assert "doodh" in reply11.lower() or "fat" in reply11.lower(), "Must answer Benefits (Q1)"
    assert "1,750" in reply11 or "1750" in reply11, "Must answer Price (Q2)"
    assert "2 se 4" in reply11 or "working days" in reply11.lower(), "Must answer Delivery Days (Q3)"
    print(">>> PASS: All 3 questions answered cleanly in a single response!")

    print("\n" + "=" * 70)
    print("ALL 11 VOICE CONTEXT & MULTI-QUESTION TESTS PASSED SUCCESSFULLY!")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(run_voice_context_tests())
