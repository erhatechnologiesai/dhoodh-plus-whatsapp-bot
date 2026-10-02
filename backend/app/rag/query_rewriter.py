import re
from typing import List, Dict, Any, Optional
from app.core.logging import logger

class QueryRewriter:
    """
    Analyzes customer queries for Doodh Plus:
    - Normalizes Roman Urdu, Urdu script, and English livestock terms
    - Handles co-references in multi-turn conversations
    - Detects primary language (Urdu script, Roman Urdu, English)
    """

    ROMAN_URDU_LIVESTOCK_SYNONYMS = {
        # Price and ordering
        "price": "price rate 1750 12500 1kg 10kg packages",
        "qeemat": "price rate 1750 12500 1kg 10kg packages",
        "qimat": "price rate 1750 12500 1kg 10kg packages",
        "keemat": "price rate 1750 12500 1kg 10kg packages",
        "rate": "price rate 1750 12500 1kg 10kg packages",
        "kitny ka": "price rate cost 1750 12500",
        "kitne ka": "price rate cost 1750 12500",
        "packing": "small pack 1kg 1750 big pack 10kg 12500",
        "order": "order booking name address phone free delivery cash on delivery cod",
        "delivery": "free home delivery across pakistan 3 to 5 days cash on delivery cod",
        "cod": "cash on delivery pay on receiving parcel",
        
        # Dosage & Usage
        "khorak": "dosage 100g large animals cows buffaloes 20 to 30g small animals goats sheep",
        "istamal": "dosage how to use mix in wanda dalia khal fodder",
        "istemal": "dosage how to use mix in wanda dalia khal fodder",
        "tariqa": "method of feeding morning evening feed",
        "kitna dena": "daily dosage 100 grams cows buffaloes 20 to 30 grams goats sheep",

        # Animal types
        "gaye": "cows large animals 100g dosage",
        "bhains": "buffaloes large animals 100g dosage milk yield fat snf",
        "bakri": "goats small animals 20 to 30g dosage",
        "bheyr": "sheep small animals 20 to 30g dosage",
        "bachhra": "calves rapid growth weight booster",
        "katta": "calves rapid growth weight booster",

        # Diseases & Benefits
        "hamla": "pregnant animals safe fetal development milk fever",
        "gabban": "pregnant animals safe fetal development milk fever",
        "gaban": "pregnant animals safe fetal development milk fever",
        "heat": "heat problems reproductive cycle hormones artificial insemination semen failure",
        "semen": "repeat breeding failed artificial insemination fertility",
        "sadoo": "mastitis udder swelling inflammation zinc selenium immunity",
        "sado": "mastitis udder inflammation protection",
        "jeer": "placenta easy expulsion post calving recovery",
        "mitti": "pica syndrome licking soil dung walls mineral deficiency",
        "gobar": "pica syndrome licking dung walls mineral deficiency",
        "deewar": "pica syndrome licking walls mineral deficiency",
        "chatna": "pica syndrome mineral deficiency cure",
        "doodh": "milk yield fat snf thick milk mammary glands",
        "dhood": "doodh milk yield fat snf mineral mixture",
        "dhoodh": "doodh milk yield fat snf mineral mixture",
        "fat": "milk fat snf higher market rate thick milk",
        "snf": "milk quality snf solid not fat",
        "course": "full course rule golden rule do not leave incomplete 10kg pack",
        "rabta": "allah ho traders contact 03339697189 03259694309 bahria town lahore",
        "aoa": "greeting salam walaikum assalam allah ho traders",
        "salam": "greeting salam walaikum assalam allah ho traders",
        "stock": "stock available 1kg 1750 10kg 12500 fresh supply",
        "batu": "batao details information explanation",
        "bara": "baray mein about information"
    }

    @staticmethod
    def detect_language(text: str) -> str:
        if not text:
            return "Roman Urdu"
        urdu_chars = sum(1 for c in text if '\u0600' <= c <= '\u06ff')
        if urdu_chars > len(text) * 0.3:
            return "Urdu"

        lower = text.lower().strip()
        # Greetings are always Roman Urdu / Urdu
        if lower in ["aoa", "salam", "slam", "assalam", "aslam", "aslamoalikum", "assalamoalaikum", "hi", "hello"]:
            return "Roman Urdu"

        roman_urdu_words = {
            "hai", "ha", "hain", "kya", "kia", "mujhe", "chahiye", "kitna", "kitni", "kitne",
            "ka", "ki", "ke", "ko", "se", "mein", "main", "ma", "par", "pe", "nahi", "ni", "hoga",
            "hogi", "batao", "bataen", "batu", "shukriya", "acha", "theek", "mera", "meri", "mere",
            "aap", "ap", "apka", "apki", "apke", "tum", "yeh", "woh", "konsa", "kese", "kaise",
            "karein", "karo", "raha", "janwar", "doodh", "dhood", "dhoodh", "khorak", "rate",
            "qeemat", "keemat", "bhains", "gaye", "bakri", "gaban", "bara", "baray", "aoa", "salam", "stock"
        }
        words = set(re.findall(r'\b[a-zA-Z]+\b', lower))
        overlap = words.intersection(roman_urdu_words)
        if len(overlap) >= 1:
            return "Roman Urdu"

        # Check if contains standard english sentences
        english_words = {"what", "how", "when", "where", "why", "who", "which", "is", "are", "the", "please", "tell", "price", "delivery"}
        eng_overlap = words.intersection(english_words)
        if len(eng_overlap) >= 2:
            return "English"

        # Default to Roman Urdu for Pakistani WhatsApp users
        return "Roman Urdu"

    @classmethod
    def rewrite_query_with_context(
        cls,
        current_query: str,
        recent_messages: List[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        detected_lang = cls.detect_language(current_query)
        cleaned_query = current_query.strip()
        search_terms = [cleaned_query]

        lower_query = cleaned_query.lower()
        for ru_key, eng_expansion in cls.ROMAN_URDU_LIVESTOCK_SYNONYMS.items():
            if re.search(r'\b' + re.escape(ru_key) + r'\b', lower_query):
                search_terms.append(eng_expansion)

        context_entities = []
        if recent_messages:
            entity_pattern = (
                r'\b(?:Doodh\s+Plus|Dhoodh\s+Plus|Bhains|Buffalo|Gaye|Cow|Bakri|Goat|'
                r'Bhed|Sheep|Bachhra|Katta|Calf|Camel|Horse|Mitti|Pica|Deewar|'
                r'Saaro|Mastitis|Heat|Semen|Jeer|Placenta|Gaban|Pregnant|'
                r'10kg|1kg|Price|Rate|Khorak|Dosage)\b'
            )
            for msg in reversed(recent_messages[-6:]):
                content = msg.get("content", "")
                potential = re.findall(entity_pattern, content, re.IGNORECASE)
                for p in potential:
                    if p.lower() not in [e.lower() for e in context_entities]:
                        context_entities.append(p)

        has_pronoun_or_referent = bool(re.search(r'\b(ye|yeh|wo|woh|iska|iski|iske|uska|uski|uske|isay|usay|isko|usko|this|that|it|inhein|unhein)\b', lower_query))
        is_short = len(cleaned_query.split()) <= 6
        if (is_short or has_pronoun_or_referent) and context_entities:
            # Inject primary context entity (e.g. Bhains, Gaye, Bakri, Mitti)
            search_terms.insert(0, context_entities[0])

        search_terms.insert(0, "Doodh Plus Allah Ho Traders")
        final_search_query = " ".join(search_terms)

        logger.info(f"Query rewrite: original='{current_query}', expanded='{final_search_query}', lang={detected_lang}")

        return {
            "original_query": current_query,
            "search_query": final_search_query,
            "detected_language": detected_lang,
            "context_entities": context_entities
        }
