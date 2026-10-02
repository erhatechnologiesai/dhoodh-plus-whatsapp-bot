import time
import re
from typing import List, Dict, Any, Optional, Tuple
from abc import ABC, abstractmethod
from app.core.config import settings
from app.core.logging import logger
from app.services.rag_service import rag_service

try:
    from openai import AsyncOpenAI
except ImportError:
    AsyncOpenAI = None

# ==============================================================================
# MASTER SYSTEM INSTRUCTIONS & APPROVED KNOWLEDGE BASE
# ==============================================================================
SYSTEM_PROMPT_TEMPLATE = """# DOODH PLUS — OFFICIAL SYSTEM INSTRUCTIONS (ALLAH HO TRADERS)

You are the official WhatsApp assistant for Allah Ho Traders and the product "Doodh Plus".
Your job is to answer customer questions naturally, accurately, and directly using ONLY the approved Doodh Plus knowledge provided below.

==================================================
IMPORTANT BEHAVIOR RULES
==================================================

1. First understand the customer's actual question.
2. Answer exactly what the customer asked.
3. Do not give a fixed or robotic answer.
4. Do not unnecessarily ask the customer to repeat or clarify if the answer already exists in the knowledge base.
5. Keep normal WhatsApp replies short, clear, conversational, and helpful (1 to 4 short paragraphs).
6. If the customer asks multiple questions, answer all of them.
7. Support Urdu, Roman Urdu, and English.
8. If the customer speaks through voice, treat the transcribed voice text exactly like a normal customer message.
9. Reply in the same language/style the customer uses whenever practical:
   - Urdu script (اردو رسم الخط) -> reply in natural Urdu script.
   - Roman Urdu -> reply in natural Pakistani Roman Urdu as a helpful sales/support representative.
   - English -> reply in clear, polite English.
10. In Roman Urdu, sound like a helpful Pakistani sales/support representative, not like a machine.
    - NEVER say "I am a bot" or "I am an AI assistant".
    - Do not sound like a machine.
11. Never invent information, percentages, medical claims, dosage, prices, ingredients, guarantees, or benefits that are not present in this knowledge base.
12. Never claim a specific percentage increase in milk because no fixed milk-increase percentage is provided in the approved knowledge.
13. When benefits depend on the animal, explain the relevant benefit for that animal instead of giving one generic answer.
14. Never diagnose a sick animal. If the customer describes a serious illness, emergency, severe weakness, infection, unusual symptoms, or asks about replacing veterinary treatment, advise them to consult a qualified veterinarian.
15. Doodh Plus should be presented as a mineral mixture / nutritional supplement, not as a replacement for veterinary medicines or professional veterinary diagnosis.
16. Do not exaggerate the product beyond the approved information.
17. Never say "100 percent guaranteed result" or promise an exact result.
18. When asked about ordering, price, delivery, or dosage, give the exact approved information.
19. If information is not available in this knowledge base, clearly say:
    "Is specific cheez ki confirmed information mere paas available nahi hai. Aap chahen to main Allah Ho Traders ki team se confirm karwane mein help kar sakta hoon."
20. Do not overwhelm the customer with all product information unless they specifically ask for full details.
21. NO EMOJIS: Use clean, professional plain text.

==================================================
CONVERSATION STYLE
==================================================

Bad robotic response:
"Please specify animal type and requirement."

Better natural response:
"Ji, Doodh Plus dono purposes mein useful bataya gaya hai. Doodh dene wali gai ya bhains mein ye doodh ki quantity aur quality support karta hai, jabke bachron, bakriyon aur bheiron ki growth stage mein body growth aur weight gain mein support karta hai. Aap kis janwar ke liye pooch rahe hain?"

Always answer the known part first, then ask a follow-up question only if needed.

==================================================
APPROVED PRODUCT KNOWLEDGE
==================================================

PRODUCT NAME: Doodh Plus
BRAND: Allah Ho Traders
HEAD OFFICE: Bahria Town, Lahore
CONTACT NUMBERS: 03339697189, 03259694309

PRODUCT TYPE:
Mineral mixture and growth-support nutritional supplement for livestock.

MAIN PURPOSE:
The product is intended to help address mineral and nutritional deficiencies in animals. It supports milk quantity and milk quality, animal health, growth, reproductive health, digestion, stamina, and immunity.

SUITABLE ANIMALS:
- Large animals: Cow, Buffalo, Camel, Horse.
- Small animals: Goat, Sheep, Calves, Young buffalo calves / growing young livestock.

MAIN INGREDIENTS / NUTRITIONAL COMPONENTS:
Calcium, Phosphorus, Vitamin A, Vitamin D3, Vitamin E, Trace minerals (Zinc, Copper, Cobalt, Iodine, Manganese, Selenium), Probiotics, Buffers.
Do not invent exact ingredient concentrations because they are not provided.

MILK BENEFITS:
For lactating cows and buffaloes, Doodh Plus supports improved milk production, milk quality, milk fat, SNF, thicker/richer milk, and mammary gland activity.
If customer asks: "Doodh kitna barhe ga?" or percentage:
Do NOT give a percentage!
Reply: "Approved information ke mutabiq koi fixed percentage mention nahi hai, kyun ke result janwar ki breed, current diet, health aur mineral deficiency par depend karta hai. Regular use se doodh ki production mein noticeable improvement 10 se 15 din mein nazar aa sakti hai."

GROWTH AND WEIGHT BENEFITS:
For calves, young buffalo calves, goats and sheep in growth stage: supports stronger bone structure, physical development, growth, body weight / body condition, and nutrient utilization.
If customer asks: "Kya gosht barhe ga? / Doodh barhe ga ya gosht?":
Reply: "Ji, dono ka use animal ke type par depend karta hai. Doodh dene wali gai ya bhains mein Doodh Plus doodh ki quantity aur quality ko support karta hai. Growing bachray, katay, bakri ya bheir mein ye growth aur body weight support karne ke liye use hota hai. Aap kis janwar ke liye lena chah rahe hain?"
Do not promise an exact weight gain.

REPRODUCTIVE SUPPORT:
Supports reproductive nutrition, heat cycle concerns, and repeated breeding/AI failure.
Never claim that Doodh Plus guarantees pregnancy.
Say: "Isay reproductive nutrition aur mineral deficiency support ke liye describe kiya gaya hai, lekin pregnancy ya fertility issue ki medical diagnosis ke liye veterinarian se check karwana zaroori hai."

PREGNANT ANIMALS:
Can be used for pregnant animals for nutritional support of the mother and developing fetus.
If the animal has pregnancy complications, advise them to confirm with their veterinarian.

STAMINA, HEALTH & IMMUNITY:
Supports weakness after milking, general stamina, body condition, seasonal stress, coat condition, and immune system. Do not claim that it cures or prevents all diseases.

PICA (EATING SOIL, DUNG, WALLS):
Licking or eating soil, dung, walls, clothes, or sand is linked with mineral deficiency. Doodh Plus provides mineral support to correct this deficiency. If severe, advise veterinary check-up.

DIGESTION:
Supports digestion, beneficial gut bacteria, and nutrient absorption.

PLACENTA / AFTER CALVING:
Provides nutritional support for easier placenta expulsion after delivery.
If placenta is retained / has not passed, say: "Is condition mein veterinarian se jaldi contact karna zaroori hai. Doodh Plus nutritional support ke liye use hota hai, emergency veterinary treatment ka replacement nahi hai."

DOSAGE:
- Large animals (Cow, Buffalo, Camel, Horse): 100 grams daily (approx. half a cup). Mix with wanda, daliya, khal, green fodder or feed (morning or evening).
- Small animals (Goat, Sheep, Calf, young livestock): 20 to 30 grams daily (approx. 2 tablespoons). Mix with normal feed or wanda.
Never change dosage based on guesswork.

HOW LONG UNTIL RESULTS:
- 7 to 10 days: general improvement in appearance, activity, and digestion.
- 10 to 15 days: noticeable improvement in milk production.
Result depends on health, diet, and existing deficiency. Never guarantee 100%.

SEASONAL USE:
May be used in both summer and winter (supports heat, fatigue, and cold stress).

PRICING:
- 1 KG pack: Rs. 1,750
- 10 KG pack: Rs. 12,500
10 KG pack is economical for commercial farms and multiple animals (lower per-kg cost).

DELIVERY:
- Free Home Delivery across Pakistan.
- Cash on Delivery (COD) available (pay upon receiving parcel).
- Delivery timeline: 2 to 4 working days.

ORDER INFORMATION:
Collect: Customer name, Complete address, Phone number, Required pack (1kg or 10kg).

COURSE / CONTINUOUS USE:
Continuous and regular use is recommended for sustainable results.

<OFFICIAL_KNOWLEDGE_BASE>
{context}
</OFFICIAL_KNOWLEDGE_BASE>
"""

# ==============================================================================
# URDU SCRIPT TO ROMAN URDU NORMALIZER (For Voice Transcription & Intent Matching)
# ==============================================================================
URDU_REPLACEMENTS = [
    # Full greetings & well-being
    ("السلام علیکم ورحمۃ اللہ وبرکاتہ", "salam"),
    ("السلام علیکم ورحمتہ اللہ وبرکاتہ", "salam"),
    ("السلام علیکم ورحمۃ اللہ", "salam"),
    ("السلام علیکم ورحمتہ اللہ", "salam"),
    ("السلام علیکم", "assalam o alaikum"),
    ("وعلیکم السلام ورحمۃ اللہ وبرکاتہ", "walaikum salam"),
    ("وعلیکم السلام ورحمتہ اللہ وبرکاتہ", "walaikum salam"),
    ("وعلیکم السلام", "walaikum assalam"),
    ("علیکم السلام", "walaikum assalam"),
    ("کیا حال چال ہے", "kya haal chaal hai"),
    ("کیا حال ہے", "kya hal ha"),
    ("طبیعت صحت ٹھیک ہے", "tabiyat theek hai"),
    ("طبیعت کیسی ہے", "tabiyat theek hai"),
    ("طبیعت صحت", "tabiyat theek"),
    ("اور سناؤ", "aur sunao kya hal ha"),
    ("اور سنائیں", "aur sunayein kya hal ha"),
    ("میں بھی ٹھیک ہوں", "main theek hoon"),
    ("میں بھی ٹھیک", "main theek hoon"),
    ("کیسے ہو", "kaise ho"),
    ("کیسے ہیں", "kaise hain"),
    ("کیا چل رہا ہے", "kya chal raha hai"),
    ("خیریت سے ہیں", "khairiyat se hain"),
    
    # Company & Product
    ("دوده پلس", "doodh plus"),
    ("دودھ پلس", "doodh plus"),
    ("اللہ ہو ٹریڈرز", "allah ho traders"),
    ("اللہ ہو", "allah ho"),
    ("دوده", "doodh"),
    ("دودھ", "doodh"),
    ("منرل مکسچر", "mineral mixture"),
    ("منرل", "mineral"),
    ("مکسچر", "mixture"),

    # Delivery Timeline & Days (Urdu & Punjabi Voice Transcriptions)
    ("کتنے دن تک میرے گھر ا جائے", "delivery timeline kitne din kab aayega"),
    ("کتنے دن تک میرے پاس پہنچ جائے", "delivery timeline kitne din kab aayega"),
    ("کتنے دنوں میں پہنچ جائے گا", "delivery timeline kitne din kab aayega"),
    ("کتنے دن تک پہنچ جائے گا", "delivery timeline kitne din kab aayega"),
    ("کتنے دن میں آئے گا", "delivery timeline kitne din kab aayega"),
    ("کتنے دن میں ملے گا", "delivery timeline kitne din kab aayega"),
    ("کتنے دن لگیں گے", "delivery timeline kitne din kab aayega"),
    ("کتنے دن لگتے ہیں", "delivery timeline kitne din kab aayega"),
    ("کتنے دن بعد ملے گا", "delivery timeline kitne din kab aayega"),
    ("کتنے دن میں پہنچے گا", "delivery timeline kitne din kab aayega"),
    ("کب تک ا جائیگا", "delivery timeline kab aayega"),
    ("کب تک آ جائے گا", "delivery timeline kab aayega"),
    ("کب تک پہنچے گا", "delivery timeline kab aayega"),
    ("کب تک ملے گا", "delivery timeline kab aayega"),
    ("کب تک آئے گا", "delivery timeline kab aayega"),
    ("کدوں تک ملے گا", "delivery timeline kab aayega"),
    ("کدوں آؤ گا", "delivery timeline kab aayega"),
    ("کنے دناں چ آوے گا", "delivery timeline kitne din kab aayega"),
    ("کنے دناں چ ملے گا", "delivery timeline kitne din kab aayega"),
    ("کنے دن لگن گے", "delivery timeline kitne din kab aayega"),
    ("کدوں پونچے گا", "delivery timeline kab aayega"),
    ("کدوں تک اپڑے گا", "delivery timeline kab aayega"),
    
    # Delivery Charges & Free Home Delivery
    ("کیا فری ڈیلیوری ہے", "delivery charges free delivery"),
    ("کیا ڈلیوری فری ہے", "delivery charges free delivery"),
    ("ڈلیوری کے پیسے", "delivery charges"),
    ("ڈیلیوری کے پیسے", "delivery charges"),
    ("ڈلیوری کا خرچہ", "delivery charges"),
    ("ڈیلیوری کا خرچہ", "delivery charges"),
    ("ڈلیوری چارجز", "delivery charges"),
    ("ڈیلیوری چارجز", "delivery charges"),
    ("ڈلیوری چارجس", "delivery charges"),
    ("ڈیلیوری چارجس", "delivery charges"),
    ("ڈلیوری فیس", "delivery charges"),
    ("ڈیلیوری فیس", "delivery charges"),
    ("ڈیلیوری مفت ہے", "delivery charges free delivery"),
    ("ڈلیوری مفت ہے", "delivery charges free delivery"),
    ("گھر پہنچانے کے پیسے", "delivery charges"),
    ("پہنچانے کے کتنے پیسے", "delivery charges"),

    # How to buy / Order inquiry
    ("کیسے لے سکتے ہیں", "kaise le sakte hain order kaise karein"),
    ("کہاں سے ملے گا", "kahan se milega order kaise karein"),
    ("کہاں سے ملے گی", "kahan se milega order kaise karein"),
    ("کہاں سے خریدیں", "kahan se milega order kaise karein"),
    ("کہاں سے خرید سکتے ہیں", "kahan se milega order kaise karein"),
    ("کیسے خریدیں", "order kaise karein"),
    ("کیسے خرید سکتے ہیں", "order kaise karein"),
    ("کس طرح ملے گا", "order kaise milega"),
    ("کیسے حاصل کریں", "order kaise karein"),
    ("کیسے منگوائیں", "order kaise karein"),
    ("آپ سے کیسے لیں", "aap se kaise le sakte hain"),
    ("کیسے منگوا سکتے ہیں", "order kaise karein"),
    ("کیسے ارڈر کریں", "order kaise karein"),
    ("کیسے آرڈر کریں", "order kaise karein"),
    ("ارڈر کیسے کریں", "order kaise karein"),
    ("آرڈر کیسے کریں", "order kaise karein"),
    ("ارڈر کا طریقہ", "order ka tariqa"),
    ("آرڈر کا طریقہ", "order ka tariqa"),
    ("منگوانے کا طریقہ", "order ka tariqa"),
    ("خریدنے کا طریقہ", "order ka tariqa"),
    ("لینے کا طریقہ", "order ka tariqa"),
    ("ارڈر کرنا ہے", "order karna hai"),
    ("آرڈر کرنا ہے", "order karna hai"),
    ("منگوانا ہے", "order mangwana hai"),
    ("لینا ہے", "order lena hai"),
    ("خریدنا ہے", "order khareedna hai"),
    ("ایک کلو بھیج دیں", "1kg order bhej dein"),
    ("دس کلو بھیج دیں", "10kg order bhej dein"),
    ("بھیج دیں", "order bhej dein"),
    ("بھجوا دیں", "order bhej dein"),
    ("پارسل بھیج دیں", "order bhej dein"),
    ("ارڈر بک کر دیں", "order book kar dein"),
    ("آرڈر بک کر دیں", "order book kar dein"),

    # Voice transcription quirks & Urdu phrases
    ("تفریح کے کتنے پیسے ہیں", "delivery charges kitne hain"),
    ("تفریح کے کتنے پیسے", "delivery charges kitne hain"),
    ("تفریح کے", "delivery charges"),
    ("تفریح", "delivery"),
    ("اڈر کتنا ہے", "order kitna hai price"),
    ("اڈر کرنا ہے", "order karna hai"),
    ("اڈر", "order"),
    ("ارڈر", "order"),
    ("آرڈر", "order"),
    ("اوڈر", "order"),
    ("گائے بھینس کے علاوہ", "gaye bhains k ilawa dusray janwar"),
    ("علاوہ بھی کسی کو", "k ilawa dusray janwar"),
    ("اس کے علاوہ", "iske ilawa"),
    ("کسی اور جانور", "kisi aur janwar"),
    ("دوسرے جانور", "dusray janwar"),
    ("دودھ بڑھانے کے لیے", "doodh barhane k liye"),
    ("دودھ بڑھاتا ہے", "doodh barhata hai"),
    ("دودھ زیادہ کرے گا", "doodh barhata hai"),
    ("دودھ میں اضافہ", "doodh barhata hai"),
    ("دودھ کم ہے", "doodh kam hai"),
    ("دودھ کم دیتی ہے", "doodh kam hai"),
    ("کتنا دودھ بڑھے گا", "doodh kitna barhe ga percentage"),
    ("دودھ کتنا بڑھے گا", "doodh kitna barhe ga percentage"),
    ("کتنے فیصد بڑھے گا", "kitne percent barhe ga"),
    ("دودھ بڑھے گا یا گوشت", "doodh barhe ga ya gosht"),
    ("کیا گوشت بڑھے گا", "kya gosht bhare ga"),
    ("گوشت بڑھے گا", "kya gosht bhare ga"),
    ("گائے کو کتنا دینا ہے", "gaye dosage 100 gram"),
    ("بھینس کو کتنا دینا ہے", "bhains dosage 100 gram"),
    ("بکری کو کتنا دینا ہے", "bakri dosage 20-30 gram"),
    ("بچھڑے کو کتنا دینا ہے", "bachhra dosage 20-30 gram"),
    ("کٹے کو کتنا دینا ہے", "katta dosage 20-30 gram"),
    ("کتنا کھلانا ہے", "dosage kitna khilana hai"),
    ("کتنا دینا ہے", "dosage kitna dena hai"),
    ("طریقہ استعمال", "dosage tariqa istemal"),
    ("استعمال کا طریقہ", "dosage tariqa istemal"),
    ("کھلانے کا طریقہ", "dosage tariqa istemal"),
    ("قیمت کتنی ہے", "price kitni hai"),
    ("کتنے کا ہے", "price kitne ka hai"),
    ("کتنے کی ہے", "price kitne ka hai"),
    ("کیا ریٹ ہے", "price kya rate hai"),
    ("کیا قیمت ہے", "price kya rate hai"),
    ("ریٹ بتا دیں", "price rate bata dein"),
    ("کتنے پیسے ہیں", "price kitne paise hain"),
    ("ایک کلو کتنے کا ہے", "1kg price kitne ka hai"),
    ("دس کلو کتنے کا ہے", "10kg price kitne ka hai"),
    ("گبن جانور کو دے سکتے ہیں", "gaban pregnant animal"),
    ("حاملہ جانور کو دے سکتے ہیں", "hamla pregnant animal"),
    ("گابھن جانور", "gaban pregnant animal"),
    ("پیٹ میں بچہ", "pregnant animal"),
    ("مٹی کھاتا ہے", "mitti chatna pica"),
    ("مٹی کھاتی ہے", "mitti chatna pica"),
    ("دیوار چاٹتی ہے", "deewar chatna pica"),
    ("گوبر کھاتا ہے", "gobar chatna pica"),
    ("اینٹیں چاٹتی ہے", "mitti deewar chatna pica"),
    ("کپڑے چباتی ہے", "kapray pica"),
    ("جیر نہیں گرائی", "jeer placenta ruki hui"),
    ("جیر رک گئی", "jeer placenta ruki hui"),
    ("جیر گراتا ہے", "jeer placenta"),
    ("پلاسنٹا", "placenta"),
    ("ہیٹ میں نہیں اتی", "heat cycle infertility"),
    ("ہیٹ میں نہیں آ رہی", "heat cycle infertility"),
    ("سیمن نہیں ٹھہرتا", "semen repeat breeding"),
    ("بار بار پھر جاتی ہے", "repeat breeding AI failure"),
    ("کراس نہیں ٹھہرتی", "repeat breeding AI failure"),
    ("ساڑو کا علاج", "saaro mastitis"),
    ("ساڑو کے لیے", "saaro mastitis"),
    ("تھنوں میں سوجن", "than mastitis sozish"),
    ("کتنے دن میں اثر کرے گا", "kitne din mein result timing"),
    ("کتنے دن میں رزلٹ آئے گا", "kitne din mein result timing"),
    ("کتنے دن میں فرق پڑے گا", "kitne din mein farq padega"),
    ("کتنے دن میں فرق نظر آئے گا", "kitne din mein farq padega"),
    ("کس کمپنی کا ہے", "brand company name"),
    ("کونسی کمپنی کا ہے", "brand company name"),
    ("کون سا برانڈ ہے", "brand company name"),
    ("کمپنی کا نام", "brand company name"),
    ("فون نمبر", "contact phone number"),
    ("رابطہ نمبر", "contact phone number"),
    ("موبائل نمبر", "contact phone number"),
    ("کال کرنی ہے", "contact phone number call"),
    ("دفتر کہاں ہے", "office kahan hai location"),
    ("دکان کہاں ہے", "shop location kahan"),
    ("ہیڈ آفس کہاں ہے", "head office location"),
    ("بہریہ ٹاؤن لاہور", "bahria town lahore"),
    ("اجزاء کیا ہیں", "ingredients formula"),
    ("فارمولا کیا ہے", "ingredients formula"),
    ("کیا ملا ہوا ہے", "ingredients formula"),
    ("وٹامنز", "vitamins"),
    ("کیلشیم", "calcium"),
    ("پینے والا دودھ", "peenay wala fresh milk"),
    ("کچا دودھ", "peenay wala fresh milk"),
    ("تازہ دودھ", "peenay wala fresh milk"),
    ("کیا آپ بوٹ ہو", "bot identity"),
    ("کیا آپ روبوٹ ہو", "bot identity"),
    ("آپ کون ہیں", "bot identity"),
    ("تم کون ہو", "bot identity"),
    ("کون بات کر رہا ہے", "bot identity"),
    ("انسان ہو یا بوٹ", "bot identity"),
    ("اللہ حافظ", "allah hafiz"),
    ("خدا حافظ", "khuda hafiz"),
    ("بہت شکریہ", "bohat shukriya"),
    ("شکریہ", "shukriya"),
    ("جزاک اللہ", "jazakallah"),
    ("الحمدللہ", "alhamdulillah"),
    ("اللہ کا شکر", "allah ka shukar"),
    ("ٹھیک ہے", "theek hai"),
    ("بہت اچھا", "bohat acha"),
    ("زبردست", "zabardast")
]

def normalize_urdu_script_to_roman(text: str) -> str:
    res = text
    for urdu, roman in URDU_REPLACEMENTS:
        res = res.replace(urdu, f" {roman} ")
    return " ".join(res.split())

# ==============================================================================
# LANGUAGE DETECTION HELPER
# ==============================================================================
def detect_language(text: str) -> str:
    """
    Returns 'urdu', 'english', or 'roman_urdu'.
    """
    # 1. Urdu script detection
    urdu_chars = len(re.findall(r'[؀-ۿݐ-ݿﭐ-﷿ﹰ-﻿]', text))
    alpha_chars = len(re.findall(r'[a-zA-Z؀-ۿ]', text))
    if urdu_chars >= 2 or (alpha_chars > 0 and urdu_chars / alpha_chars > 0.25):
        return "urdu"
    
    # 2. English detection
    text_lower = text.lower()
    english_words = {
        "what", "how", "much", "is", "the", "price", "rate", "cost", "benefits", "benefit",
        "does", "it", "work", "for", "cow", "buffalo", "goat", "sheep", "dosage", "can",
        "i", "use", "pregnant", "animal", "delivery", "cash", "order", "hello", "hi",
        "good", "morning", "afternoon", "evening", "please", "help", "who", "are", "you"
    }
    roman_urdu_markers = {
        "hai", "hain", "ha", "hn", "hoon", "hu", "kya", "kia", "kitna", "kitne", "kitnay",
        "bhai", "janwar", "chahiye", "chahye", "faida", "faide", "faiday", "khorak",
        "dein", "dena", "gaye", "gai", "bhains", "bhens", "bakri", "bhed", "bachhra",
        "wanda", "daliya", "mitti", "achi", "acha", "theek", "thk", "shukriya", "batao",
        "bataen", "btao", "karo", "karein", "mein", "me", "ko", "ka", "ki", "ke", "se",
        "sa", "par", "pe", "hota", "hoti", "hote", "gaban", "gabhan", "kahan", "kab", "ye", "wo"
    }
    words = set(re.findall(r'\b[a-z]+\b', text_lower))
    eng_matches = len(words.intersection(english_words))
    urdu_matches = len(words.intersection(roman_urdu_markers))
    
    if eng_matches >= 2 and urdu_matches == 0:
        return "english"
    
    return "roman_urdu"

# ==============================================================================
# NATURAL FALLBACK RESPONSES (Rule 19 Compliant)
# ==============================================================================
OUT_OF_DOMAIN_APOLOGIES_ROMAN = [
    "Is specific cheez ki confirmed information mere paas available nahi hai. Aap chahen to main Allah Ho Traders ki team se confirm karwane mein help kar sakta hoon.",
    "Ji bhai, main Allah Ho Traders se Doodh Plus ke hawale se hazir hoon. Agar janwaron ke doodh, khorak, price ya order ke mutaliq koi sawal ho to batayein."
]

OUT_OF_DOMAIN_APOLOGIES_URDU = [
    "اس مخصوص چیز کی تصدیق شدہ معلومات فی الحال دستیاب نہیں ہیں۔ آپ چاہیں تو میں اللہ ہو ٹریڈرز کی ٹیم سے معلوم کروا سکتا ہوں۔",
    "جی محترم، میں اللہ ہو ٹریڈرز کی جانب سے دودھ پلس منرل مکسچر کے متعلق حاضر ہوں۔ اگر آپ جانوروں کے دودھ، خوراک، قیمت یا آرڈر کے متعلق کچھ پوچھنا چاہتے ہیں تو ضرور بتائیں۔"
]

OUT_OF_DOMAIN_APOLOGIES_ENG = [
    "Confirmed information for this specific detail is not available in our records. If you wish, I can help confirm it with the Allah Ho Traders team.",
    "Hello! I am here from Allah Ho Traders regarding Doodh Plus. Feel free to ask about milk production, dosage, prices, or placing an order."
]

_apology_rotation_idx = 0

def get_next_out_of_domain_apology(lang: str = "roman_urdu") -> str:
    global _apology_rotation_idx
    if lang == "urdu":
        pool = OUT_OF_DOMAIN_APOLOGIES_URDU
    elif lang == "english":
        pool = OUT_OF_DOMAIN_APOLOGIES_ENG
    else:
        pool = OUT_OF_DOMAIN_APOLOGIES_ROMAN
    msg = pool[_apology_rotation_idx % len(pool)]
    _apology_rotation_idx = (_apology_rotation_idx + 1) % len(pool)
    return msg

UNCLEAR_VOICE_APOLOGIES = [
    "معذرت بھائی، وائس میں آواز صاف نہیں آئی۔ مہربانی کر کے دوبارہ وائس کر دیں یا لکھ کر بتا دیں۔",
    "بھائی آواز تھوڑی مدہم تھی، پلیز دوبارہ وائس بھیج دیں یا لکھ کر میسج کر دیں۔"
]

UNCLEAR_VOICE_APOLOGIES_ROMAN = [
    "Mazaarat bhai, voice mein awaaz saaf nahi aayi. Meharbani karke dobara voice kar dein ya likh kar bata dein.",
    "Bhai awaaz thori madham thi, please dobara voice note bhej dein ya likh kar message kar dein."
]

_voice_rotation_idx = 0

def get_next_unclear_voice_apology(lang: str = "urdu") -> str:
    global _voice_rotation_idx
    pool = UNCLEAR_VOICE_APOLOGIES_ROMAN if lang == "roman_urdu" else UNCLEAR_VOICE_APOLOGIES
    msg = pool[_voice_rotation_idx % len(pool)]
    _voice_rotation_idx = (_voice_rotation_idx + 1) % len(pool)
    return msg

EMOJI_PATTERN = re.compile(
    '['
    '\U00010000-\U0010FFFF'
    '\u2600-\u26FF'
    '\u2700-\u27BF'
    '\u2300-\u23FF'
    '\u2B50'
    '\u200D'
    '\uFE0F'
    '\uFE0E'
    ']+',
    flags=re.UNICODE
)

def strip_emojis(text: str) -> str:
    if not text:
        return ""
    cleaned = EMOJI_PATTERN.sub("", text)
    cleaned = re.sub(r' +', ' ', cleaned)
    cleaned = re.sub(r'\s+([,!?.:])', r'\1', cleaned)
    return cleaned.strip()

# ==============================================================================
# BASE & OPENAI PROVIDERS
# ==============================================================================
class BaseLLMProvider(ABC):
    @abstractmethod
    async def generate_response(
        self,
        system_prompt: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.2,
        is_voice: bool = False
    ) -> Dict[str, Any]:
        pass

class OpenAILLMProvider(BaseLLMProvider):
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.LLM_API_KEY
        self.model = model or settings.LLM_MODEL
        if not self.api_key or self.api_key.startswith("sk-your") or self.api_key.startswith("sk-proj-your"):
            self.client = None
        else:
            self.client = AsyncOpenAI(api_key=self.api_key)

    async def generate_response(
        self,
        system_prompt: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.2,
        is_voice: bool = False
    ) -> Dict[str, Any]:
        if not self.client:
            return await DoodhPlusKnowledgeEngine().generate_response(system_prompt, messages, temperature, is_voice=is_voice)

        start_time = time.time()
        formatted_messages = [{"role": "system", "content": system_prompt}]
        for m in messages:
            formatted_messages.append({"role": m["role"], "content": m["content"]})

        try:
            resp = await self.client.chat.completions.create(
                model=self.model,
                messages=formatted_messages,
                temperature=temperature,
                max_tokens=400
            )
            content = resp.choices[0].message.content or ""
            latency_ms = round((time.time() - start_time) * 1000, 2)
            usage = {
                "prompt_tokens": resp.usage.prompt_tokens if resp.usage else 0,
                "completion_tokens": resp.usage.completion_tokens if resp.usage else 0,
                "total_tokens": resp.usage.total_tokens if resp.usage else 0
            }
            return {
                "content": content,
                "latency_ms": latency_ms,
                "model": self.model,
                "usage": usage
            }
        except Exception as e:
            logger.error(f"LLM API error: {e}. Falling back to Doodh Plus Knowledge Engine.")
            return await DoodhPlusKnowledgeEngine().generate_response(system_prompt, messages, temperature, is_voice=is_voice)

# ==============================================================================
# DOODH PLUS AUTHORITATIVE KNOWLEDGE ENGINE
# ==============================================================================
class DoodhPlusKnowledgeEngine(BaseLLMProvider):
    """
    Authoritative knowledge engine strictly aligned with Allah Ho Traders' Master System Instructions.
    Enforces natural sales/support persona, animal-specific dosage, no percentage milk increase claims,
    no-guarantee discipline, and strict multi-language support (Urdu, Roman Urdu, English).
    """
    async def generate_response(
        self,
        system_prompt: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.2,
        is_voice: bool = False
    ) -> Dict[str, Any]:
        start_time = time.time()
        last_raw = messages[-1].get("content", "") if messages else ""
        if isinstance(last_raw, dict):
            last_msg = str(last_raw.get("content", ""))
        else:
            last_msg = str(last_raw)
        text_lower = last_msg.lower().strip()

        # Contextual prompt handling: If customer says "batao", "batu", "btao", "bta dein"
        if text_lower in ["batao", "batu", "btao", "btau", "bato", "bata do", "batao na", "bataiye", "bata dein", "bta do", "bata"]:
            for m in reversed(messages[:-1]):
                if m.get("role") in ["user", "USER"]:
                    raw_prev = m.get("content", "")
                    if isinstance(raw_prev, dict):
                        prev_txt = str(raw_prev.get("content", "")).strip().lower()
                    else:
                        prev_txt = str(raw_prev).strip().lower()
                    if prev_txt and prev_txt not in ["batao", "batu", "btao", "btau", "bato", "bata do"]:
                        last_msg = prev_txt
                        text_lower = last_msg
                        break

        # Extract previous assistant message for anti-repetition
        prev_assistant_msg = ""
        for m in reversed(messages[:-1]):
            if m.get("role") in ["assistant", "ASSISTANT"]:
                raw_c = m.get("content", "")
                if isinstance(raw_c, dict):
                    prev_assistant_msg = str(raw_c.get("content", "")).strip()
                else:
                    prev_assistant_msg = str(raw_c).strip()
                break

        # Multi-turn conversation context: extract animal and topic mentioned earlier
        context_animal = None
        context_topic = None
        for m in reversed(messages[:-1]):
            raw_prev = m.get("content", "")
            prev_content = str(raw_prev.get("content", "")) if isinstance(raw_prev, dict) else str(raw_prev)
            p_lower = prev_content.lower()

            if not context_animal:
                if any(w in p_lower for w in ["bhains", "buffalo", "بھینس"]):
                    context_animal = "bhains"
                elif any(w in p_lower for w in ["gaye", "cow", "گائے"]):
                    context_animal = "gaye"
                elif any(w in p_lower for w in ["bakri", "bakra", "goat", "بکری"]):
                    context_animal = "bakri"
                elif any(w in p_lower for w in ["bhed", "bheyr", "sheep", "بھیڑ"]):
                    context_animal = "bhed"
                elif any(w in p_lower for w in ["bachhra", "katta", "calf", "بچھڑا", "کٹہ"]):
                    context_animal = "bachhra"
                elif any(w in p_lower for w in ["camel", "oont", "اونٹ"]):
                    context_animal = "camel"
                elif any(w in p_lower for w in ["ghora", "horse", "گھوڑا"]):
                    context_animal = "ghora"

            if not context_topic:
                if any(w in p_lower for w in ["mitti", "deewar", "gobar", "pica", "مٹی", "دیوار"]):
                    context_topic = "mitti"
                elif any(w in p_lower for w in ["saaro", "sado", "mastitis", "ساڑو"]):
                    context_topic = "saaro"
                elif any(w in p_lower for w in ["heat", "semen", "کراس", "تاؤ"]):
                    context_topic = "heat"
                elif any(w in p_lower for w in ["doodh", "milk", "fat", "دودھ", "فیٹ"]):
                    context_topic = "doodh"
                elif any(w in p_lower for w in ["gaban", "pregnant", "حاملہ", "گبن"]):
                    context_topic = "gaban"
                elif any(w in p_lower for w in ["price", "rate", "kitne ka", "قیمت", "ریٹ"]):
                    context_topic = "price"

            if context_animal and context_topic:
                break

        # Detect User Language
        lang = detect_language(last_msg)

        # Helper to select text based on user language
        def choose_lang(urdu_str: str, roman_str: str, eng_str: str = "") -> str:
            if lang == "urdu":
                return urdu_str
            elif lang == "english" and eng_str:
                return eng_str
            else:
                return roman_str

        # Normalize Roman Urdu variations & typos
        normalized_text = (
            text_lower
            .replace("kha sa", "kahan se")
            .replace("kha se", "kahan se")
            .replace("kaha sa", "kahan se")
            .replace("kaha se", "kahan se")
            .replace("kidhar sa", "kahan se")
            .replace("mila ga", "milega")
            .replace("mila g", "milega")
            .replace("milay ga", "milega")
            .replace("milayga", "milega")
            .replace("miley ga", "milega")
            .replace("mil ga", "milega")
            .replace("la sakta", "le sakta")
            .replace("la sakty", "le sakta")
            .replace("la sakte", "le sakta")
            .replace("la skta", "le sakta")
            .replace("la sktay", "le sakta")
            .replace("la sakti", "le sakta")
            .replace("le skta", "le sakta")
            .replace("lay sakta", "le sakta")
            .replace("kasa", "kaisa")
            .replace("kasa ha", "kaisa hai")
            .replace("kesa", "kaisa")
            .replace("kisi", "kaisa")
            .replace("ap sa", "aap se")
            .replace("aap sa", "aap se")
            .replace("ap se", "aap se")
            .replace("nhe", "nahi")
            .replace("nhi", "nahi")
            .replace("nai", "nahi")
            .replace("oder", "order")
            .replace("ordr", "order")
            .replace("dana", "dena")
            .replace("chahye", "chahiye")
            .replace("chahia", "chahiye")
            .replace("dewwar", "deewar")
            .replace("dewar", "deewar")
            .replace("diwar", "deewar")
            .replace("chatti", "chatna")
            .replace("chati", "chatna")
            .replace("chatte", "chatna")
            .replace("chaat", "chatna")
            .replace("khati", "khana")
            .replace("khate", "khana")
            .replace("dhoodh", "doodh")
            .replace("dhood", "doodh")
            .replace("dhud", "doodh")
            .replace("chiya", "chahiye")
            .replace("chaye", "chahiye")
            .replace("chaiye", "chahiye")
            .replace("batu", "batao")
            .replace("btao", "batao")
            .replace("btayein", "bataen")
            .replace("bara ma", "baray mein")
            .replace("bare me", "baray mein")
            .replace("kia", "kya")
            .replace("kya ha ha", "kya hal ha")
            .replace("kya hal h", "kya hal ha")
            .replace("kya haal h", "kya hal ha")
            .replace("eent", "deewar")
            .replace("pathar", "mitti")
            .replace("kns ah", "konsa")
            .replace("knsa", "konsa")
            .replace("knsi", "konsi")
            .replace("gabban", "gaban")
            .replace("gabhan", "gaban")
            .replace("treeqa", "tariqa")
            .replace("tareeqa", "tariqa")
            .replace("tarika", "tariqa")
            .replace("treeqe", "tariqa")
            .replace("kaisy", "kaise")
            .replace("poucha", "poocha")
            .replace("order karny", "order karne")
            .replace("kitnay", "kitne")
            .replace("kitny", "kitne")
            .replace("kitna ka", "kitne ka")
            .replace("fawayed", "faiday")
            .replace("fawaid", "faiday")
            .replace("fawaed", "faiday")
            .replace("fayed", "faiday")
            .replace("yr", "")
            .replace("la saktay", "le sakte")
            .replace("la sakti", "le sakti")
            .replace("la saken", "le sakein")
            .replace("hm", "hum")
        )

        # Convert Urdu script characters to Roman Urdu equivalents for intent matching
        urdu_roman_converted = normalize_urdu_script_to_roman(text_lower)
        normalized_text = f"{normalized_text} {urdu_roman_converted}".strip()

        # -------------------------------------------------------------
        # 0. GREETINGS & WELL-BEING LOGIC
        # -------------------------------------------------------------
        salam_keywords = [
            "aoa", "salam", "assalam", "slaam", "aslam", "slam", "asslamoalaikum",
            "aslamualikum", "salamalikum", "wsalam", "slm", "adaab", "asslam"
        ]
        has_salam = any(
            re.search(r'\b' + re.escape(g) + r'\b', text_lower)
            for g in salam_keywords
        ) or text_lower.startswith(("aoa", "salam", "assalam", "aslam", "slam", "slaam")) or "السلام" in last_msg or "سلام" in last_msg

        hello_keywords = [
            "hello", "hi", "hey", "hy", "helo", "hlo", "hlw", "hii", "hiii", "hellow", "holla", "ہیلو", "ہائے"
        ]
        has_hello = (
            text_lower in ["h", "hi", "hy", "hey", "hello", "helo", "hlo", "hlw", "hii", "hiii", "ہیلو", "ہائے"] or
            any(re.search(r'\b' + re.escape(g) + r'\b', text_lower) for g in hello_keywords) or
            any(re.search(r'\b' + re.escape(g) + r'\b', normalized_text) for g in hello_keywords) or
            text_lower.startswith(("hi ", "hello ", "hey ", "hy ", "helo ", "hlo ", "h ", "ہیلو ", "ہائے "))
        )

        ack_regex = r'\b(ma|main|mai|me)\s*(b|bhi)?\s*(theek|thk|thek|fit|sahi)\s*(hoon|hoo|hu|houn|hn)?\b|\b(theek|thk|thek)\s*(hoon|hoo|hu|houn|hn)\b|\b(alhamdulillah|alhamdullilah|shukar|allah\s*ka\s*shukar)\b|\b(theek\s*thak|thk\s*thak|fit\s*fat)\b'
        has_acknowledgment = bool(re.search(ack_regex, normalized_text)) or any(w in text_lower or w in normalized_text for w in [
            "shakuriya", "shakriya", "shukrya", "shukriya", "shukria", "shukran", "shukurya", "thanks", "thank you", "thx", "jazakallah", "jazak allah", "ni bs", "nahi bas", "شکریہ", "جزاک اللہ"
        ]) or text_lower in [
            "thk", "theek", "thek", "fit", "sahi", "good", "fine", "alhamdulillah", "shukar", "ok", "acha", "theek hai", "thk hai", "thk h", "ٹھیک"
        ]

        hal_patterns = [
            r'\b(kia|kya)\s+(hal|haal|hall)\b',
            r'\b(kaise|kese|kaisay|kesay)\s+ho\b',
            r'\bhal\s+chal\b', r'\bhaal\s+chaal\b',
            r'\bhow\s+are\s+you\b',
            r'\bap\s+sunao\b', r'\baap\s+sunayein\b',
            r'\bkhairiyat\b',
            r'\b(theek|thk)\s+ho\b',
            r'کیا حال', r'حال چال', r'کیسے ہو', r'کیسے ہیں', r'خیریت'
        ]
        has_hal = any(bool(re.search(p, normalized_text)) for p in hal_patterns) and not has_acknowledgment

        clean_for_greeting = urdu_roman_converted if urdu_roman_converted else text_lower
        greeting_words_pat = r'\b(aoa|salam|assalam|slaam|aslam|slam|asslamoalaikum|aslamualikum|salamalikum|wsalam|slm|adaab|hello|hi|hey|hy|hlo|hlw|helo|hii|hiii|h|o|alaikum|walekum|bhai|janab|sir|sahab|g|jee|ji|rehmatullah|rehamatullah|barkat|barkatuh|barakatuh|wa|rahmatullah|allah|rahmatullahi)\b'
        urdu_greeting_pat = r'(السلام|سلام|وعلیکم|علیکم|ورحمۃ|رحمۃ|اللہ|وبرکاتہ|برکاتہ|آداب|ہیلو|ہائے|ورحمتہ|رحمتہ)'
        clean_temp = re.sub(greeting_words_pat, '', clean_for_greeting, flags=re.IGNORECASE)
        clean_temp = re.sub(urdu_greeting_pat, '', clean_temp)
        pure_greeting_tokens = re.sub(r'[^a-zA-Z0-9\u0600-\u06FF]', '', clean_temp).strip()

        # Natural human greeting prefix based on language
        if has_salam:
            greeting_prefix = choose_lang("وعلیکم السلام! ", "Walaikum Assalam! ", "Walaikum Assalam! ")
        elif has_hello:
            greeting_prefix = choose_lang("جی بھائی! ", "Ji bhai! ", "Hello! ")
        else:
            greeting_prefix = ""

        # Product question presence check
        has_product_query = any(w in normalized_text for w in [
            "price", "rate", "cost", "qeemat", "keemat", "khorak", "dosage", "istemal", "istamal",
            "doodh", "milk", "bakri", "gaye", "bhains", "order", "book", "delivery", "konsa",
            "mitti", "deewar", "chatna", "pica", "gaban", "pregnant", "stock", "1kg", "10kg",
            "batao", "bataen", "detail", "info", "maloomat", "saaro", "mastitis", "jeer", "jair", "taao", "semen", "course", "gai", "gabhun", "den",
            "faida", "faide", "faiday", "fawaid", "benefits", "gosht", "weight", "wazan", "percent", "faisad"
        ])

        def _reply_payload(reply_text: str, with_greeting: bool = True, tokens: int = 40) -> Dict[str, Any]:
            final_text = (greeting_prefix + reply_text) if (with_greeting and greeting_prefix) else reply_text
            
            # Anti-Repetition Guard
            if prev_assistant_msg and not has_product_query:
                norm_final = " ".join(final_text.lower().split())
                norm_prev = " ".join(prev_assistant_msg.lower().split())
                if norm_final == norm_prev:
                    if any(w in text_lower for w in ["ok", "acha", "theek", "sahi", "g", "jee"]):
                        final_text = choose_lang(
                            "جی بہتر بھائی! کوئی اور سوال ہو یا آرڈر کروانا ہو تو ضرور بتائیے گا۔",
                            "Ji behtar bhai! Koi aur sawal ho ya order karwana ho to zaroor batayein.",
                            "Sure! If you have any further questions or would like to place an order, please let us know."
                        )

            return {
                "content": strip_emojis(final_text),
                "latency_ms": round((time.time() - start_time) * 1000, 2),
                "model": "doodh-plus-official-rag",
                "usage": {"total_tokens": tokens}
            }

        is_pure_greeting = (has_salam or has_hello) and not has_hal and not has_acknowledgment and len(pure_greeting_tokens) < 3

        if is_pure_greeting:
            if has_salam:
                reply = choose_lang(
                    "وعلیکم السلام! جی بھائی، بتائیں دودھ پلس کے متعلق کیا معلومات چاہیے؟",
                    "Walaikum Assalam! Ji bhai, batayein Doodh Plus ke hawale se kya maloomat chahiye?",
                    "Walaikum Assalam! Hello, how can I assist you regarding Doodh Plus today?"
                )
            else:
                reply = choose_lang(
                    "جی بھائی، بتائیں دودھ پلس کے متعلق کیا رہنمائی چاہیے؟",
                    "Ji bhai! Batayein Doodh Plus ke hawale se kya rehnumai chahiye?",
                    "Hello! How can I assist you regarding Doodh Plus today?"
                )
            return _reply_payload(reply, with_greeting=False, tokens=15)

        if has_hal and not has_product_query:
            reply = choose_lang(
                "الحمدللہ بھائی، میں بالکل ٹھیک ہوں۔ آپ سنائیں، سب خیریت ہے؟ جانوروں کے متعلق کیا معلومات چاہیے؟",
                "Alhamdulillah bhai, main theek hoon. Aap sunayein, sab theek thaak? Doodh Plus ya janwaron ke hawale se kya janna chahtay hain?",
                "Alhamdulillah, I am doing well! How are you? How can I assist you regarding Doodh Plus today?"
            )
            return _reply_payload(reply)

        # Compliment / "ok good" / "zabardast" Handling
        good_patterns = [
            r'\b(ok\s+)?good\b',
            r'\b(ok\s+)?(good|zabardast|zbrdst|nice|great|very\s*good|bht\s*acha|bohot\s*acha|bahut\s*acha)\b',
            r'\bgood\s+(ho\s*gya|ho\s*gaya|hogya|hogaya|hai|ha)\b',
            r'\bok\s+good\b',
            r'گڈ', r'زبردست', r'بہت اچھا'
        ]
        is_good_compliment = any(bool(re.search(pat, text_lower)) for pat in good_patterns) or any(bool(re.search(pat, normalized_text)) for pat in good_patterns)

        if is_good_compliment and not has_product_query:
            reply = choose_lang(
                "بہت شکریہ بھائی! اللہ پاک آپ کے مال مویشی میں برکت دے۔ جب بھی ضرورت ہو بتائیے گا۔",
                "Bohat shukriya bhai! Allah Pak aap ke maal maweshi mein barkat de. Jab bhi zaroorat ho batayein.",
                "Thank you very much! May Allah bless your livestock. Feel free to reach out whenever needed."
            )
            return _reply_payload(reply, with_greeting=False)

        # Gratitude / "shukriya" / "thanks" Handling
        gratitude_tokens = [
            "shakuriya", "shakriya", "shukriya", "shukria", "shukrya", "shukran", "shukurya", "shakria",
            "thanks", "thank you", "thankyou", "thank u", "thx", "thnx",
            "jazakallah", "jazak allah", "jazakallahu khair", "jazakallah khair"
        ]
        has_negative_refusal = any(w in text_lower for w in ["nahi", "nhe", "nahin", "kuch nahi", "kuch ni", "order nahi", "oder nhe", "ni lena", "nahi lena"])
        is_gratitude = (
            any(re.search(r'\b' + re.escape(w) + r'\b', text_lower) for w in gratitude_tokens if ' ' not in w and not any('\u0600' <= c <= '\u06ff' for c in w)) or
            any(w in text_lower for w in ["thank you", "thank u", "jazak allah", "jazakallahu khair", "jazakallah khair", "shakuriya", "shukriya", "shakriya", "shukria", "shukrya", "shukran", "shukurya", "thanks", "thx", "thnx", "jazakallah"]) or
            any(w in normalized_text for w in ["shakuriya", "shukriya", "shakriya", "shukria", "shukrya", "shukran", "thanks", "jazakallah"]) or
            any(w in last_msg for w in ["شکریہ", "بہت شکریہ", "جزاک اللہ"])
        )

        if is_gratitude and not has_negative_refusal and not has_product_query:
            reply = choose_lang(
                "بہت شکریہ بھائی! اللہ پاک آپ کو خوش رکھے۔ کوئی بھی سوال ہو تو بلا جھجھک بتائیے گا۔",
                "Bohat shukriya bhai! Khush rahein. Koi bhi sawal ho to bila-jhijhak batayein.",
                "You are most welcome! Feel free to ask if you have any questions."
            )
            return _reply_payload(reply, with_greeting=False)

        if has_acknowledgment and not has_product_query:
            is_simple_ack = any(w in text_lower for w in ["ok", "acha", "theek hai", "thk hai", "thk h", "jee", "ji"]) and not any(w in text_lower for w in ["ma b", "mai b", "main b", "theek hoon", "thk hoon", "shukar", "alhamdulillah"])
            if is_simple_ack:
                reply = choose_lang(
                    "جی بہتر بھائی! کوئی اور سوال ہو یا آرڈر کروانا ہو تو ضرور بتائیں۔",
                    "Ji behtar bhai! Koi aur sawal ho ya order karwana ho to zaroor batayein.",
                    "Sure! Let me know if you have any questions or would like to order."
                )
            else:
                reply = choose_lang(
                    "الحمدللہ بھائی! بتائیں دودھ پلس کے بارے میں کچھ پوچھنا ہے یا آرڈر کرنا ہے؟",
                    "Alhamdulillah bhai! Batayein Doodh Plus ke bare mein kuch poochna hai ya order karna hai?",
                    "Alhamdulillah! Let me know if you would like to know more about Doodh Plus or place an order."
                )
            return _reply_payload(reply)

        negative_words = [
            "ni", "nahi", "nahin", "na", "no", "nope", "kuch nahi", "kuch ni", "koi sawal nahi",
            "koi sawal ni", "koi question nahi", "koi question ni", "koi nahi", "koi ni",
            "ni bas", "nahi bas", "kuch nahi shukriya", "kuch ni shukriya", "nahi shukriya",
            "ni shukriya", "bas", "bas itna", "نہیں", "بس", "نہ"
        ]
        is_negative_closing = (
            text_lower in ["ni", "nahi", "nahin", "na", "no", "nope", "bas", "نہیں", "بس", "نہ", "g nahi", "jee nahi", "ji nahi"] or
            any(re.search(r'\b' + re.escape(w) + r'\b', text_lower) for w in negative_words)
        ) and not has_product_query

        if is_negative_closing:
            reply = choose_lang(
                "بہت شکریہ بھائی! اپنا خیال رکھیں، جب بھی ضرورت ہو رابطہ کر لیجیے گا۔",
                "Bohat shukriya bhai! Apna khayal rakhein, jab bhi zaroorat ho rabta kar lijiyega.",
                "Thank you! Take care, and feel free to reach out whenever needed."
            )
            return _reply_payload(reply, with_greeting=False)

        # Refusal / Declining
        refusal_patterns = [
            r'\b(nahi|nhe|nahin|ni|nai|nhi)\s+.*(dena|dana|lena|chahiye|mangwana|karna|krna|chahta|chahye|order|oder|ordr)\b',
            r'\b(order|oder|ordr)\s+.*(nahi|nhe|nahin|ni|nai|nhi)\s+.*(dena|dana|karna|krna|chahiye|chahta)\b',
            r'\b(order|oder|ordr)\s+(nahi|nhe|nahin|ni|nai|nhi)\s+(dena|dana|karna|krna|hai|ha)\b',
            r'\b(nahi|nhe|nahin|ni|nai|nhi)\s+(dena|dana|lena|chahiye|mangwana|karna|krna)\b',
            r'\b(nahi|nhe|nahin|ni|nai|nhi)\s+(chahiye|lena|dena|karna)\b',
            r'\b(nahi|nhe|nahin|ni|nai|nhi)\s+bhai\b',
            r'\b(filhal|abhi)\s+.*(nahi|nhe|nahin|ni|nai|nhi)\b',
            r'\b(baad\s*mein|bad\s*me)\s+(le\s*lon|dekhenge|bataunga|lenge)\b',
            r'نہیں لینا', r'آرڈر نہیں', r'نہیں چاہیے', r'نہیں دینا', r'نہیں کرنا', r'نہیں منگوانا'
        ]
        is_order_refusal = (any(bool(re.search(pat, text_lower)) for pat in refusal_patterns) or any(bool(re.search(pat, normalized_text)) for pat in refusal_patterns) or any(w in last_msg for w in ["آرڈر نہیں دینا", "نہیں لینا", "نہیں چاہیے", "نہیں دینا"])) and not has_product_query

        if is_order_refusal:
            reply = choose_lang(
                "جی بالکل کوئی مسئلہ نہیں بھائی۔ جب بھی ضرورت ہو بتائیے گا، خوش رہیں۔",
                "Ji bilkul koi masla nahi bhai. Jab bhi zaroorat ho batayein, khush rahein.",
                "No problem at all! Let us know whenever you need, have a wonderful day."
            )
            return _reply_payload(reply, with_greeting=False)

        # Animal care affirmation
        care_patterns = [
            r'\b(khiyal|khayal|dekhbhal|dhiyan)\s+.*(rakh|rkh)\b',
            r'\b(rakh|rkh)\s+.*(khiyal|khayal|dekhbhal|dhiyan)\b',
            r'\b(janwar|janwaron|mal|maveshi)\s+.*(khiyal|khayal|dekhbhal|dhiyan)\b',
            r'\b(khiyal|khayal|dekhbhal|dhiyan)\s+.*(janwar|janwaron|mal|maveshi)\b',
            r'\b(khorak|feed|chara|wanda|daliya)\s+.*(achi|theek|sahi|puri|dal|de)\b',
            r'\b(koshish|mehnat)\s+.*(puri|kar\s*rahy|kar\s*rahe|chal\s*rahi)\b',
            r'خیال رکھ', r'دیکھ بھال', r'خوراک اچھی', r'خیال تو'
        ]
        is_care_affirmation = (
            any(bool(re.search(pat, text_lower)) for pat in care_patterns) or
            any(bool(re.search(pat, normalized_text)) for pat in care_patterns) or
            any(w in text_lower for w in ["khiyal ma rakh", "khayal main rakh", "khayal me rakh", "khiyal to rakh", "khayal to rakh"])
        )

        if is_care_affirmation and not has_product_query:
            reply = choose_lang(
                "ماشاءاللہ بہت اچھی بات ہے بھائی! ساتھ میں دودھ پلس استعمال کروائیں تو دودھ اور فیٹ میں مزید اضافہ ہوگا۔",
                "MashaAllah bohat achi baat hai bhai! Sath mein Doodh Plus istemal karwayen to doodh aur fat mein mazeed behtari aayegi.",
                "MashaAllah that is great! Giving Doodh Plus alongside will further support milk yield and fat."
            )
            return _reply_payload(reply, with_greeting=False)

        # Considering / Thinking
        thinking_patterns = [
            r'\b(soch|sochta)\s+(raha|hoon|hu|kr)\b',
            r'\b(dekh|check)\s+(k|ke)\s*(bataunga|btata|batao)\b',
            r'\b(mashwara|mashwrah)\s+(kr|kar)\b',
            r'\b(baad|bad)\s*(mein|me)\s*(bataunga|btata|lenge)\b',
            r'سوچ رہا', r'دیکھ کے بتاتا', r'مشورہ کر کے'
        ]
        is_thinking = any(bool(re.search(pat, text_lower)) for pat in thinking_patterns) or any(bool(re.search(pat, normalized_text)) for pat in thinking_patterns)

        if is_thinking and not has_product_query:
            reply = choose_lang(
                "جی بالکل بھائی، تسلی سے سوچ لیں، جب بھی ضرورت ہو ہم حاضر ہیں۔ خوش رہیں!",
                "Ji bilkul bhai, tasalli se soch lein, jab bhi zaroorat ho hum hazir hain. Khush rahein!",
                "Sure, take your time! We are here whenever you need assistance."
            )
            return _reply_payload(reply, with_greeting=False)

        # Medical Emergency
        medical_emergency_patterns = [
            r'\b(tez\s*bukhar|shadeed\s*bukhar|high\s*fever|severe\s*fever)\b',
            r'\b(khara\s*nahi|khari\s*nahi|uth\s*nahi|uth\s*na\s*pa|downer|beth\s*gayi\s*uth\s*nahi)\b',
            r'\b(shadeed\s*khoon|severe\s*bleeding|khoon\s*beh)\b',
            r'\b(bacha\s*phans|difficult\s*delivery|bacha\s*andar)\b',
            r'\b(shadeed\s*saaro|severe\s*mastitis)\b',
            r'\b(zehar|zahar|poison|poisoning|kuch\s*zehreela)\b',
            r'\b(shadeed\s*bimar|serious\s*illness|emergency)\b',
            r'تیز بخار', r'کھڑا نہیں', r'کھڑی نہیں', r'اٹھ نہیں', r'خون بہہ', r'بچہ پھنس', r'شدید بیمار', r'شدید ساڑو'
        ]
        is_medical_emergency = any(bool(re.search(p, normalized_text)) for p in medical_emergency_patterns) or any(w in last_msg for w in ["زہر کھا لیا", "کھڑا نہیں ہو رہا", "کھڑی نہیں ہو رہی", "تیز بخار"])

        if is_medical_emergency:
            reply = choose_lang(
                "اس صورتحال میں دودھ پلس کے بجائے فوری کسی مستند ویٹرنری ڈاکٹر سے جانور کا معائنہ کروائیں۔",
                "Is condition mein Doodh Plus supplement ke bajaye foran kisi qualified veterinarian se animal ka check-up karwayen.",
                "In this critical situation, please immediately consult a qualified veterinarian rather than using nutritional supplements."
            )
            return _reply_payload(reply)

        # Order Details Received -> Order Confirmation
        has_phone = bool(re.search(r'\b03\d{9}\b|\b03\d{2}[\s\-]?\d{7}\b|\b\d{10,13}\b', text_lower))
        has_address_hints = any(w in text_lower for w in ["multan", "lahore", "faisalabad", "sahiwal", "gujranwala", "rawalpindi", "karachi", "chak", "tehsil", "distt", "district", "city", "shehar", "pata", "address", "goth", "village", "basti", "house", "makan", "street", "gali", "mohallah", "road"])
        is_order_details = has_phone or (has_address_hints and len(text_lower.split()) >= 3) or (len(last_msg.strip().splitlines()) >= 2 and any(c.isdigit() for c in last_msg))

        if is_order_details and not any(q in text_lower for q in ["kitna", "kitne", "price", "rate", "kya", "kia", "konsa", "kaisa", "kese"]):
            phone_match = re.search(r'(03\d{2}[-\s]?\d{7}|03\d{9}|\d{11})', last_msg)
            extracted_phone = phone_match.group(0) if phone_match else "[number]"
            
            if "10" in text_lower or "das" in text_lower:
                selected_pack = "10 KG" if lang != "urdu" else "10 کلو"
            elif "1" in text_lower or "ek" in text_lower or "one" in text_lower:
                selected_pack = "1 KG" if lang != "urdu" else "1 کلو"
            else:
                selected_pack = "1 KG / 10 KG" if lang != "urdu" else "1 کلو / 10 کلو"

            extracted_name = ""
            extracted_address = ""
            lines = [l.strip() for l in last_msg.splitlines() if l.strip()]
            if len(lines) >= 3:
                for line in lines:
                    l_low = line.lower()
                    if re.search(r'03\d{9}|03\d{2}[-\s]?\d{7}', line):
                        continue
                    elif "10kg" in l_low or "1kg" in l_low:
                        continue
                    elif any(c in l_low for c in ["multan", "lahore", "chak", "goth", "karachi", "street", "house", "road", "pata", "address"]):
                        extracted_address = re.sub(r'^(?:address|pata|location)\s*[:\-]?\s*', '', line, flags=re.I).strip()
                    elif not extracted_name:
                        extracted_name = re.sub(r'^(?:naam|name|mera naam)\s*[:\-]?\s*', '', line, flags=re.I).strip()
            
            if not extracted_name:
                name_match = re.search(r'(?:mera\s+naam|naam|name)\s*(?:hai|is)?\s*[:\-]?\s*([A-Za-z\s]+?)(?=\s*(?:hai|,|\.|\bmobile\b|\bphone\b|\baddress\b|\bpata\b|\b1kg\b|\b10kg\b|$))', last_msg, re.IGNORECASE)
                if name_match:
                    extracted_name = name_match.group(1).strip()
            
            if not extracted_address:
                addr_match = re.search(r'(?:address|pata|location)\s*(?:hai|is)?\s*[:\-]?\s*([^,\n]+?)(?=\s*(?:,||\.|\bmobile\b|\bphone\b|\b1kg\b|\b10kg\b|\bpack\b|$))', last_msg, re.IGNORECASE)
                if addr_match:
                    extracted_address = addr_match.group(1).strip()

            if not extracted_name:
                extracted_name = "Customer" if lang != "urdu" else "معزز کسٹمر"
            if not extracted_address:
                cleaned_addr = re.sub(r'03\d{2}[-\s]?\d{7}|03\d{9}|\d{11}', '', last_msg).strip(' ,.-\n')
                extracted_address = cleaned_addr if len(cleaned_addr) > 3 else "Address received"

            if lang == "urdu":
                reply = (
                    f"جی، آپ کا آرڈر نوٹ کر لیا گیا ہے۔\n"
                    f"پراڈکٹ: دودھ پلس ({selected_pack})\n"
                    f"نام: {extracted_name} | موبائل: {extracted_phone}\n"
                    f"پتہ: {extracted_address}\n"
                    f"ادائیگی: کیش آن ڈیلیوری (فری ہوم ڈیلیوری)"
                )
            elif lang == "english":
                reply = (
                    f"Your order has been recorded.\n"
                    f"Product: Doodh Plus ({selected_pack})\n"
                    f"Name: {extracted_name} | Mobile: {extracted_phone}\n"
                    f"Address: {extracted_address}\n"
                    f"Payment: Cash on Delivery (Free Home Delivery)"
                )
            else:
                reply = (
                    f"Ji, aapka order note kar liya gaya hai.\n\n"
                    f"Product: Doodh Plus ({selected_pack})\n"
                    f"Naam: {extracted_name}\n"
                    f"Mobile: {extracted_phone}\n"
                    f"Address: {extracted_address}\n"
                    f"Payment: Cash on Delivery (Free Home Delivery)"
                )
            return _reply_payload(reply, with_greeting=False)

        # Fresh drinking milk clarification
        if any(w in normalized_text for w in ["peenay wala", "peene wala", "liquid doodh", "fresh doodh", "kacha doodh", "asli doodh", "peenay k liye"]):
            reply = choose_lang(
                "نہیں بھائی، یہ پینے والا دودھ نہیں بلکہ جانوروں کے لیے منرل مکسچر پاؤڈر ہے جو دودھ بڑھانے کے لیے دیا جاتا ہے۔",
                "Nahi bhai, ye peenay wala doodh nahi balkay janwaron ke liye mineral mixture powder hai jo doodh aur sehat barhane ke liye diya jata hai.",
                "No, this is not fresh drinking milk. It is a nutritional mineral mixture powder for livestock to support milk and health."
            )
            return _reply_payload(reply)

        # Location inquiry
        if any(w in normalized_text for w in ["ap kahan", "aap kahan", "office kahan", "shop kahan", "location", "address kahan", "dukan kahan", "head office", "lahore mein kahan", "kahan baithtay"]):
            reply = choose_lang(
                "ہمارا مین آفس اللہ ہو ٹریڈرز، بحریہ ٹاؤن لاہور میں ہے۔ پورے پاکستان میں فری ہوم ڈیلیوری دستیاب ہے۔",
                "Hamara main office Allah Ho Traders, Bahria Town Lahore mein hai. Pooray Pakistan mein Free Home Delivery dastiyab hai.",
                "Our main office is Allah Ho Traders, located in Bahria Town, Lahore. Free Home Delivery is available across Pakistan."
            )
            return _reply_payload(reply)

        # Bot identity / "Are you a bot" (CRITICAL: NEVER say "I am a bot" or "I am an AI assistant")
        bot_identity_patterns = [
            r'\b(bot|ai|robot|machine)\b',
            r'\b(ap|aap|tum)\s+kon\s+(ho|hain|hn)\b',
            r'\b(ap|aap)\s+ka\s+naam\b',
            r'\bwho\s+are\s+you\b',
            r'\bare\s+you\s+a?\s*(bot|ai|robot|human|real)\b',
            r'\bwho\s+is\s+this\b',
            r'کون ہو', r'کون ہیں', r'بوٹ', r'روبوٹ', r'مشین', r'کون بات کر رہا'
        ]
        is_bot_identity = any(bool(re.search(pat, text_lower)) for pat in bot_identity_patterns) or any(bool(re.search(pat, normalized_text)) for pat in bot_identity_patterns)

        if is_bot_identity:
            reply = choose_lang(
                "جی بھائی، میں اللہ ہو ٹریڈرز کی ٹیم سے بات کر رہا ہوں۔ دودھ پلس کے متعلق معلومات یا آرڈر کے لیے حاضر ہوں۔ بتائیں کیا رہنمائی کروں؟",
                "Ji bhai, main Allah Ho Traders ki team se baat kar raha hoon. Doodh Plus ki maloomat ya order ke hawale se hazir hoon. Batayein kis cheez mein help chahiye?",
                "Hello! I am from the Allah Ho Traders team. I am here to help you with Doodh Plus information and orders. How can I assist you today?"
            )
            return _reply_payload(reply, with_greeting=False)

        # Farewell
        if any(w in normalized_text for w in ["allah hafiz", "khuda hafiz", "take care", "bye bye", "alwida"]) or any(w in last_msg for w in ["اللہ حافظ", "خدا حافظ", "الوداع"]):
            reply = choose_lang(
                "اللہ حافظ بھائی! اپنا اور اپنے جانوروں کا خیال رکھیں۔ جب بھی ضرورت ہو بتائیے گا۔",
                "Allah Hafiz bhai! Apna aur apne janwaron ka khayal rakhein. Jab bhi zaroorat ho batayein.",
                "Goodbye! Take care of yourself and your animals. Feel free to contact us whenever needed."
            )
            return _reply_payload(reply, with_greeting=False)

        # Product Quality
        product_quality_patterns = [
            r'\b(apka|aapka|ap\s*ka)\s+(doodh|dhood|product|formula)\s+(kaisa|kasa|kesa|theek|acha)\b',
            r'\b(doodh|dhood|product|formula)\s+(kaisa|kasa|kesa)\s+(hai|ha)\b',
            r'\b(kaisa|kasa|kesa|kaisi|kasi)\s+(result|product|formula|quality)\b',
            r'\b(result|quality)\s+(kaisa|kasa|kesa|kaisi|kasi)\b',
            r'\b(apka|aapka)\s+.*(kaisa|kasa|kesa)\s+(hai|ha)\b',
            r'کیسا ہے', r'کیسا رزلٹ', r'کوالٹی کیسی'
        ]
        is_product_quality = any(bool(re.search(pat, normalized_text)) for pat in product_quality_patterns) or any(w in last_msg for w in ["کیسا ہے", "کیسا رزلٹ", "پراڈکٹ کیسا ہے"])

        if is_product_quality:
            reply = choose_lang(
                "دودھ پلس اللہ ہو ٹریڈرز کا اعلیٰ کوالٹی منرل مکسچر ہے جو دودھ اور فیٹ بڑھاتا ہے۔ 10 سے 15 دن میں واضح رزلٹ دیتا ہے۔",
                "Doodh Plus Allah Ho Traders ka high-quality mineral mixture hai jo doodh aur fat support karta hai aur 10 se 15 din mein noticeable result deta hai.",
                "Doodh Plus is Allah Ho Traders' premium mineral mixture that supports milk yield and fat, showing noticeable improvement in 10 to 15 days."
            )
            return _reply_payload(reply)

        # =============================================================
        # MULTI-QUESTION & MULTI-INTENT RESOLUTION ENGINE
        # =============================================================

        is_bhains = any(w in normalized_text for w in ["bhains", "bhens", "buffalo"]) or "بھینس" in last_msg
        is_gaye = any(w in normalized_text for w in ["gaye", "gai", "cow"]) or "گائے" in last_msg
        is_small = any(w in normalized_text for w in ["bakri", "bakra", "bhed", "bheyr", "bher", "goat", "sheep", "بکری", "بھیڑ"])
        is_bachhra = any(w in normalized_text for w in ["bachhra", "bachhre", "bachhray", "katta", "katte", "kattay", "calf", "calves", "بچھڑا", "بچھڑے", "کٹہ", "کٹے"])

        if not (is_bhains or is_gaye or is_small or is_bachhra) and context_animal:
            if context_animal == "bhains":
                is_bhains = True
            elif context_animal == "gaye":
                is_gaye = True
            elif context_animal in ["bakri", "bhed"]:
                is_small = True
            elif context_animal == "bachhra":
                is_bachhra = True

        # 1. SPECIFIC FAQ: DOODH VS GOSHT / GOSHT BARHE GA
        doodh_vs_gosht_patterns = [
            r'\b(doodh|milk)\s+.*(barhe|barhay|barhta|barhega|barhayga|hoga)\s+.*(ya\s+gosht|gosht)\b',
            r'\b(gosht|wazan|weight)\s+.*(barhe|barhay|barhta|barhega|barhayga|hoga)\s+.*(ya\s+doodh|doodh)\b',
            r'\b(kya|kia)\s+gosht\s+(bhare|barhe|barhay|barhta)\b',
            r'\bgosht\s+(bhare|barhe|barhay|barhta|barhega)\b',
            r'دودھ بڑھے گا یا گوشت', r'گوشت بڑھے گا', r'کیا گوشت بڑھے گا'
        ]
        is_doodh_vs_gosht = any(bool(re.search(pat, normalized_text)) for pat in doodh_vs_gosht_patterns)

        reply_doodh_vs_gosht = choose_lang(
            "جی بھائی، دونوں کا استعمال جانور کی قسم پر منحصر ہے۔ دودھ دینے والی گائے یا بھینس میں دودھ پلس دودھ کی مقدار اور کوالٹی کو سپورٹ کرتا ہے۔ بڑھتے ہوئے بچھڑوں، کٹوں، بکریوں یا بھیڑوں میں یہ گروتھ اور جسمانی وزن سپورٹ کرنے کے لیے استعمال ہوتا ہے۔ آپ کس جانور کے لیے لینا چاہ رہے ہیں؟",
            "Ji, dono ka use animal ke type par depend karta hai. Doodh dene wali gai ya bhains mein Doodh Plus doodh ki quantity aur quality ko support karta hai. Growing bachray, katay, bakri ya bheir mein ye growth aur body weight support karne ke liye use hota hai. Aap kis janwar ke liye lena chah rahe hain?",
            "Yes, its use depends on the animal. In lactating cows and buffaloes, Doodh Plus supports milk quantity and quality. In growing calves, young buffalo calves, goats, and sheep, it supports growth and body weight. Which animal are you inquiring for?"
        )

        # 2. SPECIFIC FAQ: PERCENTAGE / MILK INCREASE AMOUNT
        percentage_milk_patterns = [
            r'\b(kitne|kitnay|kitna)\s*(percent|faisad|feesad|%)\b',
            r'\b(kitna|kitnay|kitne)\s*(doodh)\s*(barhe|barhay|barhta|ziada|barhega|barhayga)\b',
            r'\bdoodh\s+kitna\s+(barhe|barhay|barhta|barhega|barhayga)\b',
            r'\bkitne\s*percent\b',
            r'کتنا دودھ', r'دودھ کتنا', r'کتنے فیصد', r'کتنے پرسنٹ'
        ]
        is_percentage_milk = any(bool(re.search(pat, normalized_text)) for pat in percentage_milk_patterns) and not is_doodh_vs_gosht

        reply_percentage_milk = choose_lang(
            "کسی بھی تصدیق شدہ معلومات میں دودھ بڑھنے کا کوئی فکس فیصد درج نہیں ہے، کیونکہ نتیجہ جانور کی نسل، موجودہ خوراک، صحت اور کمی پر منحصر ہوتا ہے۔ باقاعدہ استعمال سے 10 سے 15 دن میں دودھ کی پیداوار میں واضح بہتری نظر آ سکتی ہے۔",
            "Approved information ke mutabiq koi fixed percentage mention nahi hai, kyun ke result janwar ki breed, current diet, health aur mineral deficiency par depend karta hai. Regular use se doodh ki production mein noticeable improvement 10 se 15 din mein nazar aa sakti hai.",
            "No fixed percentage is specified in the approved information, as results depend on the animal's breed, current feed, health, and mineral deficiency. With regular use, noticeable improvement in milk production can be seen in 10 to 15 days."
        )

        # 3. BENEFITS & MILK YIELD INTENT
        benefits_patterns = [
            r'\b(faida|faide|faiday|fawaid|fawayed|benefits)\b',
            r'\b(kya|kia)\s+(faida|faide|faiday|fawaid)\b',
            r'\b(kya|kia)\s+kaam\s+(karta|karti|karega)\b',
            r'\b(doodh|milk)\s+.*(barhana|barhane|barhata|barhay|barhe|badhana|kam\s*deti|kam\s*deta|kam\s*hai|kam\s*h)\b',
            r'\b(kam\s*deti|kam\s*deta|kam\s*doodh|doodh\s*kam|doodh\s*problem)\b',
            r'\b(fat|snf|malai|gaarha)\s+.*(barhana|barhane|barhata|barhay|barhe)\b',
            r'فائدے', r'فائدہ', r'کیا فائدہ', r'دودھ بڑھانے', r'دودھ بڑھانا', r'دودھ کم', r'کم دودھ', r'فیٹ بڑھانے'
        ]
        is_benefits = (any(bool(re.search(pat, normalized_text)) for pat in benefits_patterns) or any(w in last_msg for w in ["فائدے", "فائدہ", "کیا فائدہ", "دودھ بڑھانے", "دودھ بڑھانا"])) and not is_doodh_vs_gosht and not is_percentage_milk

        if is_bhains:
            reply_benefits = choose_lang(
                "دودھ پلس بھینس کا دودھ اور فیٹ بڑھاتا ہے، ہاضمہ ٹھیک کرتا ہے اور 10 سے 15 دن میں واضح فرق دیتا ہے۔",
                "Doodh Plus bhains mein doodh ki quantity, quality aur fat ko support karta hai, hazma behtar karta hai aur 10 se 15 din mein noticeable farq deta hai.",
                "Doodh Plus supports milk yield, quality, and fat in buffaloes, improves digestion, and shows noticeable results in 10 to 15 days."
            )
        elif is_small:
            reply_benefits = choose_lang(
                "دودھ پلس بکری کا دودھ اور صحت بہتر بناتا ہے اور 10 سے 15 دن میں نمایاں فرق دیتا ہے۔",
                "Doodh Plus bakri aur bhed mein doodh, sehat aur haddiyon ko support karta hai aur 10 se 15 din mein farq deta hai.",
                "Doodh Plus supports milk, health, and bone strength in goats and sheep with noticeable improvement in 10 to 15 days."
            )
        elif is_gaye:
            reply_benefits = choose_lang(
                "دودھ پلس گائے کا دودھ اور فیٹ بڑھاتا ہے، ہاضمہ درست کرتا ہے اور 10 سے 15 دن میں اچھا رزلٹ دیتا ہے۔",
                "Doodh Plus gai mein doodh ki quantity, quality aur fat ko support karta hai, hazma behtar karta hai aur 10 se 15 din mein farq deta hai.",
                "Doodh Plus supports milk yield, fat, and digestion in cows, showing noticeable results in 10 to 15 days."
            )
        else:
            reply_benefits = choose_lang(
                "دودھ پلس جانوروں کا دودھ اور فیٹ بڑھاتا ہے، ہاضمہ ٹھیک کرتا ہے اور 10 سے 15 دن میں واضح رزلٹ دیتا ہے۔",
                "Doodh Plus janwaron mein doodh ki quantity, quality aur fat ko support karta hai aur 10 se 15 din mein behtari dikhata hai.",
                "Doodh Plus supports milk quantity, quality, and fat in livestock, improving digestion and showing noticeable results in 10 to 15 days."
            )

        # 4. PRICE & PACKAGES INTENT
        price_patterns = [
            r'\b(price|rate|cost|qeemat|keemat|paisa|paise|rupay|rupees)\b',
            r'\b(kitne|kitnay|kitny|kine)\s*(ka|ki|k|ke|ko|mein|me|da|di)\b',
            r'\b(kitna|kitne|kitnay)\s*(kharach|kharch|lagat)\b',
            r'پرائز', r'پرائس', r'قیمت', r'ریٹ', r'کتنے کا', r'کتنے کی', r'روپے', r'پیسے', r'کی قیمت', r'کی ریٹ', r'کنے دا', r'کنے دی'
        ]
        is_price = any(bool(re.search(pat, normalized_text)) for pat in price_patterns) or any(w in last_msg for w in ["پرائز", "پرائس", "قیمت", "ریٹ", "کتنے کا", "کتنے کی", "روپے", "پیسے"])

        reply_price = choose_lang(
            "دودھ پلس کا 1 کلو پیک 1,750 روپے اور 10 کلو پیک 12,500 روپے کا ہے۔ پورے پاکستان میں فری ہوم ڈیلیوری اور کیش آن ڈیلیوری دستیاب ہے۔",
            "1 KG pack Rs. 1,750 ka hai aur 10 KG pack Rs. 12,500 ka hai. Pakistan bhar mein free home delivery aur Cash on Delivery (COD) available hai.",
            "1 KG pack is Rs. 1,750 and 10 KG pack is Rs. 12,500. Free home delivery and Cash on Delivery are available across Pakistan."
        )

        # 5. ORDER PROCEDURE INTENT
        how_to_buy_patterns = [
            r'\b(kaise|kese|kaisay|kesay|kasa|kesa|kahan|kidhar|kha)\s+.*(order|ordr|le\s*sakt|la\s*sakt|lay\s*sakt|milega|miley\s*ga|mila\s*ga|milay\s*ga|mil\s*sakta|purchase|buy|mangwayen|mangwaya|khareed|dastiyab)',
            r'\b(order|ordr)\s+.*(kaise|kese|kaisay|kesay|kasa|kesa|kahan|kidhar|tariqa|process|karna|krna|karwana|krwana|dena|chahiye)',
            r'\b(aap\s*se|ap\s*se|ap\s*sa|aap\s*sa|ap)\s+.*(le\s*sakt|la\s*sakt|lena|mangwana|khareedna|milega|miley\s*ga|mila\s*ga|mil\s*sakta)',
            r'\b(hum|hm|ma|main|mei)\s+.*(kaise|kese|kasa|kha|kahan|kidhar)\s+.*(order|le|la|mangwa|khareed|buy|milega|mila\s*ga)',
            r'\b(kahan\s*se|kidhar\s*se|kha\s*sa|kha\s*se|kaha\s*se|kaha\s*sa)\s+.*(milega|miley\s*ga|mila\s*ga|khareed|le\s*sakt|la\s*sakt|purchase)',
            r'\b(kaise|kese|kasa|kha|kahan)\s+(milega|miley\s*ga|mila\s*ga|mil\s*sakta|mangwayen|khareedein|purchase\s*karein)',
            r'\b(lena\s*hai|mangwana\s*hai|khareedna\s*hai)\s+.*(kaise|kese|kahan|kha)',
            r'\b(order|mangwana|khareedna)\s+ka\s+(kya|kia|konsa)\s+(tariqa|tarika|treeqa|process|treeqe)',
            r'\b(order|mangwana|khareedna)\s+(kaise|kese|kaisay|kesay|kaisy)\s+(hoga|karein|kare|karte|karoon)',
            r'\b(order|ordr)\s+(karna|krna|karwana|krwana)\s+(hai|ha|chahiye|chahta)',
            r'\b(order|ordr)\s+(dena|dna)\s+(hai|ha)',
            r'\b(1kg|10kg|pack)\s+(bhej\s*dein|bhejo|mangwana|chahiye)',
            r'order kaise', r'kaise order',
            r'کیسے لے سکتے', r'کہاں سے ملے', r'کیسے ملے گا', r'کیسے منگوائیں', r'آپ سے کیسے',
            r'کیسے ارڈر', r'کیسے آرڈر', r'ارڈر کیسے', r'آرڈر کیسے', r'ارڈر کرنا', r'آرڈر کرنا', r'منگوانا ہے', r'ارڈر بھیجیں', r'بھیج دیں', r'ارڈر کا طریقہ', r'آرڈر کا طریقہ'
        ]
        is_order_procedure = (any(bool(re.search(pat, normalized_text)) for pat in how_to_buy_patterns) or any(w in last_msg for w in ["ارڈر کیسے", "آرڈر کیسے", "کیسے ارڈر", "کیسے آرڈر", "ارڈر کرنا", "آرڈر کرنا", "منگوانا ہے", "اڈر کتنا", "اڈر کرنا", "ارڈر بھیجیں", "بھیج دیں", "کیسے لیں", "کہاں سے ملے"])) and not is_order_refusal

        reply_order = choose_lang(
            "آرڈر کے لیے اپنا نام، موبائل نمبر، مکمل پتہ اور جتنا پیک چاہیے (1 کلو یا 10 کلو) بتا دیں، پارسل فری ہوم ڈیلیوری کے ساتھ روانہ کر دیں گے۔",
            "Order ke liye apna naam, mobile number, mukammal address aur required pack (1kg ya 10kg) bata dein, parcel Free Home Delivery ke sath rawana kar diya jayega.",
            "To book your order, please provide your name, mobile number, complete address, and desired pack (1kg or 10kg). We will dispatch it with Free Home Delivery."
        )

        # 6. DELIVERY TIMELINE INTENT
        delivery_timeline_patterns = [
            r'\b(parcel|order|delivery|package)\s+.*(kitne\s*din|kab\s*tak|kab\s*pohnch|kab\s*mil|kab\s*aay|kab\s*ay|kab\s*ae)\b',
            r'\b(kitne|kitnay|kitny)\s*(din|dino|dinon)\s*.*(parcel|delivery|ghar|pohnch|aay|mileg|mil\s*jay|mere\s*paas)\b',
            r'\b(kab\s*tak|kab)\s+.*(parcel|delivery|ghar|pohnch|aay|mileg|mil\s*jay|mere\s*paas)\b',
            r'\bdelivery\s+timeline\b',
            r'کتنے دن تک میرے پاس', r'کتنے دن تک میرے گھر', r'کب تک ا جائیگا', r'کب تک آ جائے گا',
            r'کتنے دنوں میں پہنچ', r'کتنے دن میں آئے گا', r'کتنے دن میں پہنچے گا', r'کب تک پہنچے گا',
            r'کب تک آئے گا', r'کتنے دن لگیں گے', r'کتنے دن لگتے ہیں', r'کتنے دن میں ملے گا',
            r'کتنے دن میں ڈلیوری', r'کتنے دن میں ڈیلیوری'
        ]
        is_delivery_timeline = any(bool(re.search(pat, normalized_text)) for pat in delivery_timeline_patterns) or any(w in last_msg for w in ["کتنے دن تک میرے پاس", "کتنے دن تک میرے گھر", "کب تک ا جائیگا", "کتنے دنوں میں پہنچ", "کتنے دن میں پہنچے گا", "کب تک پہنچے گا", "کب تک آئے گا"])

        reply_delivery_timeline = choose_lang(
            "پورے پاکستان میں پارسل 2 سے 4 ورکنگ ڈیز میں پہنچ جاتا ہے، فری ہوم ڈیلیوری اور کیش آن ڈیلیوری ہے۔",
            "Pakistan bhar mein parcel 2 se 4 working days mein pohnch jata hai, delivery free hai aur payment Cash on Delivery par hoti hai.",
            "Delivery takes 2 to 4 working days across Pakistan with Free Home Delivery and Cash on Delivery."
        )

        # 7. DELIVERY CHARGES INTENT
        delivery_charges_patterns = [
            r'\b(delivery\s*charges|delivery\s*free|delivery\s*fee|shipping\s*charges|delivery\s*ka\s*kharcha)\b',
            r'\bcharges\s+(kitne|kitnay|kya|kia|hai|ha)\b',
            r'فری ڈیلیوری', r'ڈیلیوری چارجز', r'ڈلیوری چارجز'
        ]
        is_delivery_charges = any(bool(re.search(pat, normalized_text)) for pat in delivery_charges_patterns) or any(w in last_msg for w in ["ڈیلیوری چارجز", "ڈلیوری چارجز", "فری ہے", "تفریح کے"])

        reply_delivery_charges = choose_lang(
            "پورے پاکستان میں ہوم ڈیلیوری بالکل فری ہے، ادائیگی پارسل ملنے پر کیش آن ڈیلیوری کرنی ہوگی۔",
            "Pakistan bhar mein delivery bilkul free hai, payment parcel milne par Cash on Delivery par hoti hai.",
            "Delivery is completely free across Pakistan. Payment is made via Cash on Delivery when you receive the parcel."
        )

        # 8. DOSAGE INTENT
        dosage_patterns = [
            r'\b(khorak|dosage|istemal|istamal|tariqa|tarika|treeqa|tareeqa|khilana|khilane)\b',
            r'\b(kitna|kitni|kaise|kese)\s+.*(dena|deni|dein|den|khilana|khilani|use|khilayein)\b',
            r'\b(kitna|kitni)\s+(den|dein|khilayein|khilaye)\b',
            r'خوراک', r'کتنا دینا', r'کتنا دیں', r'کیسے کھلانا', r'طریقہ استعمال', r'استعمال کا طریقہ'
        ]
        is_dosage = any(bool(re.search(pat, normalized_text)) for pat in dosage_patterns) or any(w in last_msg for w in ["خوراک", "کتنا دینا", "کیسے کھلانا", "طریقہ استعمال"])

        if is_gaye:
            reply_dosage = choose_lang(
                "گائے کو روزانہ 100 گرام (تقریباً آدھا کپ) ونڈے، دلیے، کھل یا چارے میں اچھی طرح مکس کر کے دیں۔",
                "Gai ko rozana 100 gram Doodh Plus dein. Isay wanda, daliya, khal ya charay mein achi tarah mix karke de sakte hain.",
                "Give 100 grams daily of Doodh Plus for cows, mixed well into wanda, daliya, khal, or feed."
            )
        elif is_bhains:
            reply_dosage = choose_lang(
                "بھینس کو روزانہ 100 گرام (تقریباً آدھا کپ) ونڈے، دلیے، کھل یا چارے میں اچھی طرح مکس کر کے دیں۔",
                "Bhains ko rozana 100 gram Doodh Plus dein. Isay wanda, daliya, khal ya charay mein achi tarah mix karke de sakte hain.",
                "Give 100 grams daily of Doodh Plus for buffaloes, mixed well into wanda, daliya, khal, or feed."
            )
        elif is_small:
            reply_dosage = choose_lang(
                "بکری یا بھیڑ کے لیے روزانہ 20 سے 30 گرام (تقریباً دو چمچ) معمول کی خوراک یا ونڈے میں مکس کر کے دیں۔",
                "Bakri ya bhed ke liye rozana 20 se 30 gram (taqreeban 2 chammach) recommended hai. Isay uski normal feed ya wanda mein mix karke dein.",
                "For goats or sheep, 20 to 30 grams daily (approx. 2 tablespoons) is recommended, mixed into their normal feed."
            )
        elif is_bachhra:
            reply_dosage = choose_lang(
                "بچھڑے یا کٹے کو روزانہ 20 سے 30 گرام (تقریباً دو چمچ) خوراک یا دلیے میں مکس کر کے دیں۔",
                "Bachray ya katay ke liye rozana 20 se 30 gram (taqreeban 2 chammach) recommended hai. Isay unki feed ya daliya mein mix karke dein.",
                "For calves or young buffalo calves, give 20 to 30 grams daily mixed into their feed or daliya."
            )
        else:
            reply_dosage = choose_lang(
                "بڑے جانور (گائے، بھینس) کو روزانہ 100 گرام اور چھوٹے جانور (بکری، بچھڑا) کو روزانہ 20 سے 30 گرام چارے یا ونڈے میں مکس کر کے دیں۔",
                "Barray janwar (gai, bhains) ko rozana 100 gram aur chotay janwar (bakri, bachhra) ko 20 se 30 gram feed ya wanda mein mix karke dein.",
                "Give 100 grams daily for large animals (cow, buffalo) and 20 to 30 grams daily for small animals (goat, calf) mixed with feed."
            )

        # 9. RESULT TIMING INTENT
        result_timing_patterns = [
            r'\b(result|results|asar|farq)\s+.*(kitne\s*din|kab\s*tak|kitnay\s*din)\b',
            r'\b(kitne|kitnay|kitny)\s*(din|dino|dinon)\s*.*(result|asar|farq|doodh\s*barh)\b',
            r'کتنے دن میں رزلٹ', r'کتنے دن میں اثر', r'کتنے دن میں فرق', r'کتنے دن میں فرق پڑے گا'
        ]
        is_result_timing = any(bool(re.search(pat, normalized_text)) for pat in result_timing_patterns) and not is_delivery_timeline and not is_percentage_milk

        reply_result_timing = choose_lang(
            "باقاعدہ استعمال سے 7 سے 10 دن میں ہاضمہ، چستی اور صحت میں بہتری نظر آتی ہے، اور 10 سے 15 دن میں دودھ اور فیٹ میں واضح اضافہ ہوتا ہے۔",
            "Approved information ke mutabiq regular use se 7 se 10 din mein activity, digestion aur overall condition mein improvement nazar aati hai, jabke doodh ki production mein 10 se 15 din mein noticeable farq nazar aa sakta hai.",
            "Noticeable improvement in activity, digestion, and body condition can be seen in 7 to 10 days, and in milk production within 10 to 15 days."
        )

        # 10. BRAND INTENT
        brand_patterns = [
            r'\b(brand|company|maker|manufacturer)\b',
            r'\b(konsa|konsi|kya|kia)\s+(brand|company|adara|idara)\b',
            r'برانڈ', r'کمپنی کا نام', r'کونسی کمپنی', r'کس کمپنی'
        ]
        is_brand = any(bool(re.search(pat, normalized_text)) for pat in brand_patterns) or any(w in last_msg for w in ["برانڈ", "کمپنی کا نام", "کس کمپنی کا ہے", "کونسا برانڈ"])

        reply_brand = choose_lang(
            "دودھ پلس اللہ ہو ٹریڈرز کا رجسٹرڈ پروڈکٹ ہے، ہمارا ہیڈ آفس بحریہ ٹاؤن لاہور میں ہے۔ رابطہ نمبر: 03339697189۔",
            "Doodh Plus Allah Ho Traders ka registered product hai. Head office Bahria Town Lahore mein hai. Contact: 03339697189.",
            "Doodh Plus is an official product of Allah Ho Traders, Bahria Town, Lahore. Contact: 03339697189."
        )

        # 11. GABAN / PREGNANCY INTENT
        gaban_patterns = [
            r'\b(pregnant|gaban|gabban|gabhan|gabhun|hamla|hamal|bacha|pet mein)\b',
            r'حاملہ', r'گبن', r'گابھن'
        ]
        is_gaban = any(bool(re.search(pat, normalized_text)) for pat in gaban_patterns) or any(w in last_msg for w in ["حاملہ", "گبن", "گابھن"])

        reply_gaban = choose_lang(
            "جی بالکل، دودھ پلس گبن جانور کے لیے مفید ہے اور پیٹ میں بچے کی نشوونما اور ہڈیوں کو طاقت دیتا ہے۔ اگر کوئی پیچیدگی ہو تو ویٹرنری ڈاکٹر سے مشورہ کر لیں۔",
            "Ji, provided product information ke mutabiq Doodh Plus pregnant animals ke liye nutritional support ke taur par use kiya ja sakta hai aur pet mein bachay ki growth ko support karta hai. Agar pregnancy complicated ho to veterinarian se confirm karna behtar hai.",
            "Yes, Doodh Plus can be used for pregnant animals for nutritional support. If there are pregnancy complications, please consult your veterinarian."
        )

        # 12. PICA INTENT (Eating soil, dung, licking walls)
        pica_patterns = [
            r'\b(mitti|miti|gobar|deewar|kapray|plastic|pica|chatna|eent|pathar)\b',
            r'مٹی', r'دیوار', r'اینٹ', r'گوبر', r'پتھر', r'چاٹ'
        ]
        is_pica = any(bool(re.search(pat, normalized_text)) for pat in pica_patterns) or any(w in last_msg for w in ["مٹی", "دیوار", "اینٹ", "گوبر", "پتھر", "چاٹ"])

        reply_pica = choose_lang(
            "مٹی، گوبر یا دیوار چاٹنا منرلز کی کمی کی وجہ سے ہو سکتا ہے۔ دودھ پلس منرل سپورٹ فراہم کرتا ہے۔ اگر عادت بہت شدید ہو تو ڈاکٹر کو بھی چیک کروائیں۔",
            "Mitti ya deewar chatna aksar mineral deficiency se related hota hai. Doodh Plus mineral support provide karta hai. Agar habit severe ho ya dusre symptoms hon to veterinarian ko bhi check karwana chahiye.",
            "Eating soil or licking walls is often linked to mineral deficiency. Doodh Plus provides vital mineral supplementation. If severe, consult a vet."
        )

        # 13. PLACENTA / JAIR INTENT
        is_placenta = any(w in normalized_text for w in ["jeer", "jer", "jair", "placenta", "sootak"]) or "جیر" in last_msg
        reply_placenta = choose_lang(
            "دودھ پلس ڈیلیوری کے بعد جیر کے باآسانی اخراج میں غذائی مدد دیتا ہے۔ اگر جیر رک گئی ہو تو فوری کسی ویٹرنری ڈاکٹر سے رجوع کریں کیونکہ یہ ایمرجنسی علاج کا متبادل نہیں ہے۔",
            "Doodh Plus delivery ke baad jair ke asan ikhraj mein nutritional support deta hai. Lekin agar jair ruki hui ho to foran veterinarian se contact karna zaroori hai kyun ke ye emergency veterinary treatment ka replacement nahi hai.",
            "Doodh Plus provides nutritional support for easier placenta expulsion. If placenta is retained, immediately contact a veterinarian."
        )

        # 14. CONTACT NUMBERS INTENT
        contact_patterns = [
            r'\b(phone\s*number|contact\s*number|apna\s*number|mobile\s*number|call\s*karni|rabta\s*number|raabta\s*number|number\s*bhej|number\s*dein)\b',
            r'رابطہ نمبر', r'فون نمبر', r'موبائل نمبر'
        ]
        is_contact = any(bool(re.search(pat, normalized_text)) for pat in contact_patterns)

        reply_contact = choose_lang(
            "اللہ ہو ٹریڈرز کے رابطہ نمبرز یہ ہیں: 03339697189 اور 03259694309۔",
            "Allah Ho Traders ke contact numbers: 03339697189 aur 03259694309.",
            "Official contact numbers for Allah Ho Traders: 03339697189 and 03259694309."
        )

        # 15. 10KG INQUIRY INTENT
        is_ten_kg = ("10kg" in normalized_text or "10 kg" in normalized_text or "das kilo" in normalized_text) and any(w in normalized_text for w in ["kyun", "faida", "faide", "reason", "benefit", "lena"])
        reply_ten_kg = choose_lang(
            "10 کلو پیک فارم یا زیادہ جانوروں کے لیے بہترین ہے اور اس میں فی کلو قیمت 1 کلو پیک کے مقابلے میں کافی کم پڑتی ہے۔",
            "10 KG pack ziada janwaron ya commercial farm ke liye behtareen hai aur is mein per-kg price 1kg pack ke muqablay mein sasti padti hai.",
            "The 10 KG pack is ideal for farms or multiple animals, offering a lower cost per kilogram."
        )

        # 16. INGREDIENTS INTENT
        is_ingredients = any(w in normalized_text for w in ["ajza", "ingredients", "formula", "composition", "kya mila", "vitamins", "minerals"])
        reply_ingredients = choose_lang(
            "دودھ پلس میں کیلشیم، فاسفورس، وٹامنز (A, D3, E)، زنک، کاپر، کوبالٹ، آیوڈین، مینگنیز، سیلینیم، پروبائیوٹکس اور بفرز شامل ہیں۔",
            "Is mein Calcium, Phosphorus, Vitamins (A, D3, E), Trace Minerals (Zinc, Copper, Cobalt, Iodine, Manganese, Selenium), Probiotics aur Buffers shamil hain.",
            "It contains Calcium, Phosphorus, Vitamins A, D3, E, trace minerals (Zinc, Copper, Cobalt, Iodine, Selenium), Probiotics, and Buffers."
        )

        # 17. INFERTILITY / HEAT INTENT
        is_heat = (
            bool(re.search(r'\b(heat|semen|taao|silent\s*heat|insemination)\b', normalized_text, flags=re.I)) or
            bool(re.search(r'(?:^|\s)(کراس|ٹھہرتا|ہیٹ|تاؤ|سیمن)(?:\s|$)', normalized_text)) or
            any(w in normalized_text for w in ["semen na thehr", "baar baar phir", "thehrna", "thehar"])
        )
        reply_heat = choose_lang(
            "دودھ پلس میں وٹامنز اور منرلز ہیں جو تولیدی نظام کو طاقت دیتے ہیں اور ہیٹ و سیمن ٹھہرنے میں مددگار ہیں۔",
            "Doodh Plus reproductive nutrition aur mineral support provide karta hai, jo heat cycle aur bar bar AI failure mein madadgar hai. Doctor se checkup bhi zaroori hai.",
            "Doodh Plus provides nutritional and mineral support for reproductive health and heat cycle support."
        )

        # 18. MASTITIS / SAARO INTENT
        is_saaro = any(w in normalized_text for w in ["saaro", "saaru", "mastitis", "hawana", "sozish", "than band", "khoon", "cheechray"]) or any(w in last_msg for w in ["ساڑو", "سوجن", "تھن", "چھچھڑے"])
        reply_saaro = choose_lang(
            "دودھ پلس تھنوں کی صحت اور ساڑو کے خلاف مدافعت بڑھاتا ہے۔ روزانہ 100 گرام دیں۔",
            "Doodh Plus thanon ki sehat aur saaro ke khilaf immunity support karta hai. Rozana 100 gram dein.",
            "Doodh Plus supports udder health and immunity against mastitis. Give 100 grams daily."
        )

        # 19. CALF GROWTH INTENT
        is_calf_growth = any(w in normalized_text for w in ["bachhra", "bachhray", "katta", "katte", "growth", "wazan", "weight", "barhotri"]) and not is_dosage and not is_doodh_vs_gosht
        reply_calf_growth = choose_lang(
            "دودھ پلس کٹوں اور بچھڑوں کی گروتھ اور ہڈیوں کو مضبوط بناتا ہے۔ روزانہ 20 سے 30 گرام دیں۔",
            "Doodh Plus bachron aur katon ki body growth, bone structure aur weight gain ko support karta hai. Rozana 20 se 30 gram dein.",
            "Doodh Plus supports bone structure, growth, and weight gain in calves. Give 20 to 30 grams daily."
        )

        # 20. COURSE DURATION INTENT
        is_course = any(w in normalized_text for w in ["course", "consistent", "chhor dein", "kitna lamba", "khatam"])
        reply_course = choose_lang(
            "بہتر اور پائیدار نتائج کے لیے پروڈکٹ کا باقاعدہ اور مسلسل استعمال تجویز کیا جاتا ہے۔",
            "Behtar aur consistent results ke liye regular use recommend kiya gaya hai, taake minerals ki kami door ho sakay.",
            "Regular and continuous use is recommended for optimal and sustainable nutritional support."
        )

        # 21. PRODUCT OVERVIEW INTENT
        product_inquiry_patterns = [
            r'\b(konsa|konsi|kya|kia)\s+(product|item|service|formula|dawa|dawaii)\b',
            r'\b(product|item|service|formula)\s+(konsa|konsi|kya|kia)\b',
            r'\b(kya|kia)\s+cheez\s+(ha|hai)\b',
            r'\b(product|products)\s+(info|detail|details|maloomat|taaruf)\b'
        ]
        is_product_overview = any(bool(re.search(pat, normalized_text)) for pat in product_inquiry_patterns) or any(w in last_msg for w in ["پراڈکٹ کون سا", "کیا چیز ہے"])
        reply_product_overview = choose_lang(
            "ہمارا پروڈکٹ 'دودھ پلس' منرل مکسچر ہے جو دودھ اور فیٹ بڑھاتا ہے۔ 1 کلو 1,750 روپے اور 10 کلو 12,500 روپے کا ہے۔",
            "Hamara product 'Doodh Plus' mineral mixture hai jo doodh aur fat support karta hai. 1 KG 1,750 aur 10 KG 12,500 Rs ka hai.",
            "Our product 'Doodh Plus' is a livestock mineral mixture supporting milk yield and fat. 1 KG is Rs. 1,750 and 10 KG is Rs. 12,500."
        )

        # =============================================================
        # MULTI-INTENT ACCUMULATION & COMBINATION (Rule 6 Compliant)
        # =============================================================
        matched_intents = []

        if is_doodh_vs_gosht:
            matched_intents.append(("doodh_vs_gosht", reply_doodh_vs_gosht))

        if is_percentage_milk:
            matched_intents.append(("percentage_milk", reply_percentage_milk))

        if is_benefits:
            matched_intents.append(("benefits", reply_benefits))

        if is_price:
            matched_intents.append(("price", reply_price))

        if is_order_procedure:
            matched_intents.append(("order", reply_order))

        if is_delivery_timeline:
            matched_intents.append(("delivery_timeline", reply_delivery_timeline))

        if is_delivery_charges and not is_price and not is_delivery_timeline:
            matched_intents.append(("delivery_charges", reply_delivery_charges))

        if is_dosage:
            if not is_benefits or any(w in normalized_text for w in ["khorak", "dosage", "kitna dena", "kitni deni", "خوراک", "کتنا دینا"]):
                matched_intents.append(("dosage", reply_dosage))

        if is_result_timing and not is_delivery_timeline and not is_benefits and not is_percentage_milk:
            matched_intents.append(("result_timing", reply_result_timing))

        if is_brand:
            matched_intents.append(("brand", reply_brand))

        if is_gaban:
            matched_intents.append(("gaban", reply_gaban))

        if is_pica:
            matched_intents.append(("pica", reply_pica))

        if is_contact:
            matched_intents.append(("contact", reply_contact))

        if is_ten_kg:
            matched_intents.append(("ten_kg", reply_ten_kg))

        if is_ingredients:
            matched_intents.append(("ingredients", reply_ingredients))

        if is_heat:
            matched_intents.append(("heat", reply_heat))

        if is_saaro:
            matched_intents.append(("saaro", reply_saaro))

        if is_calf_growth:
            matched_intents.append(("calf_growth", reply_calf_growth))

        if is_placenta:
            matched_intents.append(("placenta", reply_placenta))

        if is_course:
            matched_intents.append(("course", reply_course))

        if is_product_overview and not matched_intents:
            matched_intents.append(("product_overview", reply_product_overview))

        # Combine matched intents concisely (1-2 lines per intent, max 3)
        if matched_intents:
            selected_intents = matched_intents[:3]
            combined_reply = "\n\n".join(reply_text for _, reply_text in selected_intents)
            return _reply_payload(combined_reply)

        # -------------------------------------------------------------
        # 22. FALLBACK FOR UNCLEAR INPUT & MISSING KNOWLEDGE (Rule 19)
        # -------------------------------------------------------------
        if is_voice:
            reply = get_next_unclear_voice_apology(lang=lang)
        else:
            reply = get_next_out_of_domain_apology(lang=lang)

        # Anti-Repetition Guard
        if prev_assistant_msg and (reply.strip() == prev_assistant_msg.strip() or reply.strip()[:30] == prev_assistant_msg[:30]):
            if any(w in text_lower for w in ["ok", "acha", "theek", "sahi", "g", "jee"]):
                reply = choose_lang(
                    "جی بہتر بھائی! کوئی اور سوال ہو یا آرڈر کروانا ہو تو ضرور بتائیے گا۔",
                    "Ji behtar bhai! Koi aur sawal ho ya order karwana ho to zaroor batayein.",
                    "Sure! Feel free to ask if you have any further questions."
                )
            elif any(w in text_lower for w in ["la sakta", "le sakta", "kaise", "mangwa", "order"]):
                reply = choose_lang(
                    "جی بالکل بھائی! آرڈر کے لیے اپنا نام، پتہ اور موبائل نمبر بتا دیں، پارسل فری ہوم ڈیلیوری کے ساتھ روانہ کر دیں گے۔",
                    "Ji bilkul bhai! Order ke liye apna naam, address aur mobile number bata dein, parcel Free Home Delivery ke sath rawana kar diya jayega.",
                    "To place an order, please share your name, address, and mobile number. We will dispatch it with Free Home Delivery."
                )
            else:
                reply = choose_lang(
                    "جی بھائی، کیا آپ اس کا آرڈر بک کروانا چاہتے ہیں یا کچھ اور پوچھنا چاہتے ہیں؟",
                    "Ji bhai, kya aap iska order book karwana chahte hain ya kuch aur poochna chahte hain?",
                    "Would you like to book an order or is there anything else I can assist you with?"
                )

        return _reply_payload(reply)


# ==============================================================================
# MAIN AI SERVICE COORDINATOR
# ==============================================================================
class AIService:
    """
    Main AI Service coordinating Intent Classification, RAG retrieval,
    Context-grounded Generation, and Human Handoff detection.
    """
    def __init__(self):
        self.provider = OpenAILLMProvider()

    def detect_human_handoff(self, message: str) -> Tuple[bool, Optional[str]]:
        keywords = [
            "agent", "human", "representative", "operator", "insan se baat",
            "admin", "support person", "customer service agent", "human support",
            "نمائندے", "نمائندہ", "ایجنٹ", "انسان"
        ]
        msg_clean = message.lower()
        normalized = normalize_urdu_script_to_roman(message).lower()
        for kw in keywords:
            if kw in msg_clean or re.search(r'\b' + re.escape(kw) + r'\b', normalized):
                return True, f"Customer requested: '{kw}'"
        return False, None

    async def generate_support_response(
        self,
        query: str,
        conversation_history: List[Dict[str, str]] = None,
        system_prompt: Optional[str] = None,
        top_k: Optional[int] = None,
        similarity_threshold: Optional[float] = None,
        is_voice: bool = False
    ) -> Dict[str, Any]:
        # 1. Immediate human handoff check
        is_handoff, reason = self.detect_human_handoff(query)
        if is_handoff:
            rag_result = {
                "chunks": [],
                "is_relevant": False,
                "context_text": "",
                "latency_ms": 0.0,
                "rewritten_query": query,
                "similarity_scores": []
            }
            llm_result = await self.provider.generate_response(
                system_prompt="Connecting to Allah Ho Traders human agent",
                messages=[{"role": "user", "content": query}],
                is_voice=is_voice
            )
            return {
                "response": strip_emojis(llm_result["content"]),
                "human_handoff": True,
                "handoff_reason": reason,
                "rag_result": rag_result,
                "model": llm_result["model"],
                "latency_ms": llm_result["latency_ms"],
                "token_usage": llm_result.get("usage", {})
            }

        # 2. Retrieve relevant context via RAG
        rag_result = await rag_service.retrieve_context_for_query(
            query=query,
            recent_messages=conversation_history or [],
            top_k=top_k,
            threshold=similarity_threshold
        )

        # 3. Construct System Prompt with Knowledge Context
        prompt_template = system_prompt or SYSTEM_PROMPT_TEMPLATE
        if "{context}" in prompt_template:
            final_system_prompt = prompt_template.replace(
                "{context}",
                rag_result["context_text"] if rag_result["is_relevant"] else "NO RELEVANT KNOWLEDGE FOUND."
            )
        else:
            final_system_prompt = f"{prompt_template}\n\n<OFFICIAL_KNOWLEDGE_BASE>\n{rag_result['context_text']}\n</OFFICIAL_KNOWLEDGE_BASE>"

        if is_voice:
            final_system_prompt += (
                "\n\n[VOICE NOTE CONTEXT ACTIVE]\n"
                "- The customer's latest query was received as a WhatsApp Voice Note (transcribed to text).\n"
                "- Treat transcribed voice text exactly like a normal customer message.\n"
                "- Carefully resolve any pronouns ('ye', 'wo', 'iska', 'iski', 'isko', 'kitna') against preceding conversation history.\n"
                "- Answer PRECISELY what the customer asked without unasked topics.\n"
                "- Keep the response natural, friendly, and concise (1-4 short paragraphs). Plain text only without emojis."
            )

        # 4. Prepare message history with deduplication
        history = []
        for m in (conversation_history or []):
            role = "assistant" if m.get("role", "").lower() in ["assistant", "system"] else "user"
            history.append({"role": role, "content": m.get("content", "")})

        # Deduplicate if history already ends with this query
        if not history or history[-1].get("content", "").strip() != query.strip() or history[-1].get("role") != "user":
            history.append({"role": "user", "content": query})

        # 5. Call LLM (or Knowledge Engine fallback)
        llm_result = await self.provider.generate_response(
            system_prompt=final_system_prompt,
            messages=history,
            temperature=settings.LLM_TEMPERATURE,
            is_voice=is_voice
        )

        return {
            "response": strip_emojis(llm_result["content"]),
            "human_handoff": False,
            "handoff_reason": None,
            "rag_result": rag_result,
            "model": llm_result["model"],
            "latency_ms": llm_result["latency_ms"] + rag_result["latency_ms"],
            "token_usage": llm_result.get("usage", {})
        }

ai_service = AIService()
