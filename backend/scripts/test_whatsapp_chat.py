import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.ai_service import ai_service

test_messages = [
    "aoa",
    "salam",
    "kia hal ha ?",
    "ma b thk hoo",
    "ap ka product kns ah",
    "ap ka product knsa ha ?",
    "konsi service hai",
    "meri bakri dewwar chatti ha ?",
    "gaye mitti khati ha",
    "mujhy price btao iski",
    "10 kg pack chahiye",
    "dhood k baray ma batao",
    "gabban janwar ko de sakte hain?",
    "saaro ki bimari hai",
    "bachhre ka wazan barhana hai",
    "ajza kya hain",
    "kitne din mein asar hoga",
    "khorak kitni deni hai",
    "cricket ka score kya hai",
    "prdct",
    "Muhammad Zeeshan\n03036282495\nMultan cantt"
]

async def main():
    print("=" * 60)
    print("TESTING DOODH PLUS BOT CHAT CASES")
    print("=" * 60)
    for msg in test_messages:
        res = await ai_service.generate_support_response(msg)
        print(f"\n[USER]: {repr(msg)}")
        safe_reply = res['response'].encode('ascii', 'replace').decode()
        print(f"[BOT]:\n{safe_reply}")
        print("-" * 50)

if __name__ == "__main__":
    asyncio.run(main())
