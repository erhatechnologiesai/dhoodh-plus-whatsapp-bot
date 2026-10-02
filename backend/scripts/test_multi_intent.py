import re

URDU_REPLACEMENTS = [
    # Full greetings & well-being
    ("السلام علیکم ورحمۃ اللہ وبرکاتہ", "salam"),
    ("السلام علیکم ورحمتہ اللہ وبرکاتہ", "salam"),
    ("السلام علیکم ورحمۃ اللہ", "salam"),
    ("السلام علیکم ورحمتہ اللہ", "salam"),
    ("السلام علیکم", "assalam o alaikum"),
    ("وعلیکم السلام ورحمۃ اللہ وبرکاتہ", "walaikum salam"),
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
    ("کتنے دن تک میرے گھر آ جائے", "delivery timeline kitne din kab aayega"),
    ("کتنے دن تک میرے پاس اجائے گا", "delivery timeline kitne din kab aayega"),
    ("کتنے دن تک میرے پاس آ جائے گا", "delivery timeline kitne din kab aayega"),
    ("کتنے دن میں آئے گا", "delivery timeline kitne din kab aayega"),
    ("کتنے دن میں آ جائے گا", "delivery timeline kitne din kab aayega"),
    ("کتنے دنوں میں پہنچ", "delivery timeline kitne din kab pohnchega"),
    ("کتنے دنوں میں پہنچے گا", "delivery timeline kitne din kab pohnchega"),
    ("کتنے دن میں پہنچے گا", "delivery timeline kitne din kab pohnchega"),
    ("کب تک ا جائیگا", "delivery timeline kab aayega"),
    ("کب تک آ جائے گا", "delivery timeline kab aayega"),
    ("کب تک پہنچے گا", "delivery timeline kab pohnchega"),
    ("کب تک آئے گا", "delivery timeline kab aayega"),
    ("کب آئے گا", "delivery timeline kab aayega"),
    ("کب پہنچے گا", "delivery timeline kab pohnchega"),
    ("کتنے دن لگیں گے", "delivery timeline kitne din"),
    ("کتنے دن لگتے ہیں", "delivery timeline kitne din"),
    ("کتنے دن میں ملے گا", "delivery timeline kitne din"),
    ("کتنے دن میں ڈلیوری", "delivery timeline kitne din"),
    ("کتنے دن میں ڈیلیوری", "delivery timeline kitne din"),
    ("کتنے دن تک", "delivery timeline kitne din"),
    ("کتنے دنوں میں", "delivery timeline kitne din"),
    ("کتنے دن میں", "delivery timeline kitne din"),
    ("کتنے دن", "kitne din"),
    ("کتنے دنوں", "kitne din"),

    # Order in Urdu & Punjabi (Voice Transcriptions - longer phrases first)
    ("اچھا میں یہ کیسے ارڈر کر سکتا ہوں", "order kaise kar sakta hoon"),
    ("میں یہ کیسے ارڈر کر سکتا ہوں", "order kaise kar sakta hoon"),
    ("میں اس کو کیسے ارڈر کر سکتا ہوں", "order kaise kar sakta hoon"),
    ("اس کو کیسے ارڈر کر سکتا ہوں", "order kaise kar sakta hoon"),
    ("ارڈر کیسے کر سکتا ہوں", "order kaise kar sakta hoon"),
    ("آرڈر کیسے کر سکتا ہوں", "order kaise kar sakta hoon"),
    ("ارڈر کیسے کریں", "order kaise hoga"),
    ("آرڈر کیسے کریں", "order kaise hoga"),
    ("ارڈر کیسے کرنا ہے", "order kaise hoga"),
    ("آرڈر کیسے کرنا ہے", "order kaise hoga"),
    ("ارڈر کیسے کرنا", "order kaise hoga"),
    ("آرڈر کیسے کرنا", "order kaise hoga"),
    ("ارڈر کیسے", "order kaise"),
    ("آرڈر کیسے", "order kaise"),
    ("کیسے ارڈر کر سکتے ہیں", "order kaise hoga"),
    ("کیسے آرڈر کر سکتے ہیں", "order kaise hoga"),
    ("کیسے ارڈر کریں", "order kaise hoga"),
    ("کیسے آرڈر کریں", "order kaise hoga"),
    ("کیسے ارڈر ہوگا", "order kaise hoga"),
    ("کیسے آرڈر ہوگا", "order kaise hoga"),
    ("کیسے ارڈر", "order kaise"),
    ("کیسے آرڈر", "order kaise"),
    ("ارڈر کا طریقہ", "order ka tariqa"),
    ("آرڈر کا طریقہ", "order ka tariqa"),
    ("ارڈر کرنا پے", "order karna hai"),
    ("اڈر کتنا کرنا", "order kaise karna"),
    ("اڈر کرنا پے", "order karna hai"),
    ("ارڈر کرنا ہے", "order karna hai"),
    ("آرڈر کرنا ہے", "order karna hai"),
    ("ارڈر کرنا", "order"),
    ("آرڈر کرنا", "order"),
    ("ارڈر بک", "order"),
    ("آرڈر بک", "order"),
    ("ارڈر بھیجیں", "order bhejein"),
    ("منگوانا ہے", "order chahiye"),
    ("منگوانا", "order"),
    ("منگوائیں", "order"),
    ("بھیج دیں", "order bhejein"),
    ("بھیجو", "order bhejein"),
    ("ارڈر", "order"),
    ("آرڈر", "order"),
    ("اڈر", "order"),
    ("آڈر", "order"),
    ("اردڑ", "order"),
    ("چاہیدا", "chahiye"),
    ("چاہیدی", "chahiye"),
    ("لینا ہے", "order chahiye"),
    ("لینا", "lena"),

    # Benefits (Urdu Script - longer phrases first)
    ("مجھے اس کے فائدے بتاؤ اور اس کی پرائز بھی ساتھ بتاؤ", "faiday batao benefits price batao rate"),
    ("اس کے فائدے بھی ساتھ بتاؤ", "faiday batao benefits"),
    ("فائدے بھی ساتھ بتاؤ", "faiday batao benefits"),
    ("مجھے اس کے فائدے بتاؤ", "faiday batao benefits"),
    ("اس کے فائدے بتاؤ", "faiday batao benefits"),
    ("فائدے بتاؤ", "faiday batao benefits"),
    ("فائدے بتائیں", "faiday bataen benefits"),
    ("فائدہ بتاؤ", "faiday batao benefits"),
    ("کیا فائدہ ہے", "faida kya hai benefits"),
    ("کیا فائدے ہیں", "faiday kya hain benefits"),
    ("دودھ بڑھانے کے لیے", "doodh barhana faida"),
    ("دودھ بڑھانے", "doodh barhana"),
    ("دودھ بڑھانا", "doodh barhana"),
    ("بڑھا سکتے ہیں", "barhana"),
    ("بڑھا سکتے", "barhana"),
    ("بڑھائیں", "barhana"),
    ("بڑھایا", "barhana"),
    ("بڑھا", "barhana"),
    ("دودھ ودھاون", "doodh barhana"),
    ("دودھ ودھانا", "doodh barhana"),
    ("کم دودھ دیتی ہے", "doodh kam problem"),
    ("کم دودھ دیتی", "doodh kam problem"),
    ("دودھ نہیں دیتی", "doodh kam problem"),
    ("دودھ کم دیتی ہے", "doodh kam problem"),
    ("دودھ کم دیتی", "doodh kam problem"),
    ("دودھ کم ہے", "doodh kam problem"),
    ("دودھ سکھا گئی", "doodh kam problem"),
    ("کم دودھ", "doodh kam problem"),
    ("دودھ کی تفصیل", "doodh detail faida"),
    ("فیٹ بڑھانے", "fat barhana"),
    ("فیٹ اور ملائی", "fat barhana"),
    ("فیٹ", "fat"),
    ("گاڑھا", "gaarha"),
    ("اضافہ", "barhana"),
    ("فائدے", "faiday benefits"),
    ("فائدہ", "faida benefits"),
    ("کے فائ", "faiday"),

    # Price and Cost (Urdu & Punjabi Voice Transcriptions - longer phrases first)
    ("فیز دودھ کی جو پرائز ہے وہ مجھے بتاؤ", "doodh plus price batao"),
    ("اس کی پرائز بھی بتاؤ", "price batao rate"),
    ("اس کی پرائز بھی بتا", "price batao rate"),
    ("اس کی پرائز بتاؤ", "price batao rate"),
    ("تصویر کی قیمت کی ہے", "price kya hai"),
    ("پرائز بھی بتاؤ", "price batao rate"),
    ("پرائز بتاؤ", "price batao"),
    ("پرائز بتا", "price batao"),
    ("پرائز بتائیں", "price bataen"),
    ("پرائس بتاؤ", "price batao"),
    ("پرائس بتائیں", "price bataen"),
    ("پرائیز بتاؤ", "price batao"),
    ("ریٹ بتاؤ", "rate batao"),
    ("ریٹ بتائیں", "rate bataen"),
    ("قیمت بتاؤ", "price batao"),
    ("قیمت بتائیں", "price bataen"),
    ("کتنے کا ہے", "kitne ka hai price"),
    ("کتنے کی ہے", "kitne ki hai price"),
    ("کتنے کا", "kitne ka price"),
    ("کتنے کی", "kitne ki price"),
    ("دودھ کی پرائز", "doodh price"),
    ("دودھ کا ریٹ", "doodh price"),
    ("دودھ کی قیمت", "doodh price"),
    ("کی قیمت ہے", "price kya hai"),
    ("کی قیمت اے", "price kya hai"),
    ("کی قیمت کی ہے", "price kya hai"),
    ("کی ریٹ ہے", "rate kya hai"),
    ("کی ریٹ اے", "rate kya hai"),
    ("کی حساب ہے", "price kya hai"),
    ("کی حساب اے", "price kya hai"),
    ("کنے دا ہے", "kitne ka hai price"),
    ("کنے دا اے", "kitne ka hai price"),
    ("کنے دی اے", "kitne ki hai price"),
    ("پرائز", "price"),
    ("پرائس", "price"),
    ("پرائیز", "price"),
    ("پراّئز", "price"),
    ("قیمت", "price"),
    ("ریٹ", "rate"),
    ("پیسے", "paise"),
    ("روپے", "rupay"),
    ("لاگت", "cost"),

    # STT / Whisper quirks from real logs
    ("فیز دودھ", "doodh plus"),
    ("فیز", "doodh plus"),
    ("پھز", "doodh plus"),
    ("تفریح کے", "free delivery"),
    ("تفریح", "free delivery"),

    # Packages & Delivery
    ("ایک کلو", "1kg"),
    ("دس کلو", "10kg"),
    ("1 کلو", "1kg"),
    ("10 کلو", "10kg"),
    ("10 مہینہ", "10kg"),
    ("بچت پیک", "bachat pack"),
    ("کیش آن ڈیلیوری", "cash on delivery"),
    ("فری ہوم ڈیلیوری", "free delivery"),
    ("فری ڈیلیوری", "free delivery"),
    ("ہوم ڈیلیوری", "delivery"),
    ("ڈلیوری", "delivery"),
    ("ڈیلیوری", "delivery")
]

def normalize_urdu_script_to_roman(text: str) -> str:
    res = text
    for urdu, roman in URDU_REPLACEMENTS:
        res = res.replace(urdu, f" {roman} ")
    return " ".join(res.split())

def classify_and_answer(query: str, is_voice: bool = True):
    text_lower = query.lower().strip()
    norm = normalize_urdu_script_to_roman(text_lower)
    normalized_text = f"{text_lower} {norm}"

    matched_intents = []

    # 1. Price Intent
    price_patterns = [
        r'\b(price|rate|cost|qeemat|keemat|paisa|paise|rupay|rupees)\b',
        r'\b(kitne|kitnay|kitny|kine)\s*(ka|ki|k|ke|ko|mein|me|da|di)\b',
        r'پرائز', r'پرائس', r'قیمت', r'ریٹ', r'کتنے کا', r'کتنے کی', r'روپے', r'پیسے'
    ]
    if any(bool(re.search(pat, normalized_text)) for pat in price_patterns):
        reply = (
            "Doodh Plus ki price:\n"
            "1kg = Rs. 1,750\n"
            "10kg = Rs. 12,500\n"
            "(Pakistan bhar mein Free Home Delivery aur Cash on Delivery dastiyab hai)."
        )
        matched_intents.append(("price", reply))

    # 2. Benefits Intent
    benefits_patterns = [
        r'\b(faida|faide|faiday|fawaid|fawayed|benefits)\b',
        r'\b(kya|kia)\s+(faida|faide|faiday|fawaid)\b',
        r'\b(doodh|milk)\s+.*(barhana|barhane|barhata|barhay|barhe|badhana|kam\s*deti|kam\s*deta|kam\s*hai|kam\s*h)\b',
        r'\b(kam\s*deti|kam\s*deta|kam\s*doodh|doodh\s*kam|doodh\s*problem)\b',
        r'\b(fat|snf|malai|gaarha)\s+.*(barhana|barhane|barhata|barhay|barhe)\b',
        r'فائدے', r'فائدہ', r'کیا فائدہ', r'دودھ بڑھانے', r'دودھ بڑھانا', r'دودھ کم', r'کم دودھ', r'فیٹ بڑھانے'
    ]
    if any(bool(re.search(pat, normalized_text)) for pat in benefits_patterns):
        if "bakri" in normalized_text or "بکری" in query:
            reply = "Doodh Plus bakri ke doodh aur sehat ko support karta hai, kamzori door karta hai aur hazma theek karta hai. 10-15 din mein improvement noticeable ho sakti hai."
        elif "bhains" in normalized_text or "بھینس" in query:
            reply = "Doodh Plus bhains ke doodh ki miqdar aur fat/malai ko qudrati tor par barhata hai, hazma behtar karta hai aur kamzori door karta hai. 10-15 din mein doodh mein wazeh behtari nazar aa sakti hai."
        else:
            reply = "Doodh Plus janwaron ke doodh ki miqdar aur fat ko qudrati tor par barhata hai, hazma theek karta hai aur calcium/minerals ki kami poori karta hai. 10-15 din mein doodh mein wazeh behtari nazar aa sakti hai."
        matched_intents.append(("benefits", reply))

    # 3. Order Procedure Intent
    order_patterns = [
        r'\b(kaise|kese|kaisay|kesay|kasa|kesa|kahan|kidhar|kha)\s+.*(order|ordr|le\s*sakt|la\s*sakt|lay\s*sakt|milega|miley\s*ga|mila\s*ga|milay\s*ga|mil\s*sakta|purchase|buy|mangwayen|mangwaya|khareed|dastiyab)',
        r'\b(order|ordr)\s+.*(kaise|kese|kaisay|kesay|kasa|kesa|kahan|kidhar|tariqa|process|karna|krna|karwana|krwana|dena|chahiye)',
        r'\b(hum|hm|ma|main|mei)\s+.*(kaise|kese|kasa|kha|kahan|kidhar)\s+.*(order|le|la|mangwa|khareed|buy|milega|mila\s*ga)',
        r'order kaise', r'kaise order',
        r'کیسے لے سکتے', r'کہاں سے ملے', r'کیسے ملے گا', r'کیسے منگوائیں', r'آپ سے کیسے',
        r'کیسے ارڈر', r'کیسے آرڈر', r'ارڈر کیسے', r'آرڈر کیسے', r'ارڈر کرنا', r'آرڈر کرنا', r'منگوانا ہے', r'ارڈر بھیجیں', r'بھیج دیں', r'ارڈر کا طریقہ', r'آرڈر کا طریقہ'
    ]
    if any(bool(re.search(pat, normalized_text)) for pat in order_patterns):
        reply = "Order book karwanay ke liye apna Naam, Mobile Number, Mukammal Pata (Address) aur required pack (1kg ya 10kg) bhej dein, hum foran parcel dispatch kar dein ge."
        matched_intents.append(("order", reply))

    # 4. Delivery Timeline Intent
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
    if any(bool(re.search(pat, normalized_text)) for pat in delivery_timeline_patterns):
        reply = "Parcel poore Pakistan mein 2 se 4 working days ke andar deliver ho jata hai. Free Home Delivery aur Cash on Delivery (COD) dastiyab hai."
        matched_intents.append(("delivery_timeline", reply))

    # 5. Brand Intent
    brand_patterns = [
        r'\b(brand|company|maker|manufacturer)\b',
        r'\b(konsa|konsi|kya|kia)\s+(brand|company|adara|idara)\b',
        r'برانڈ', r'کمپنی کا نام', r'کونسی کمپنی', r'کس کمپنی'
    ]
    if any(bool(re.search(pat, normalized_text)) for pat in brand_patterns):
        reply = "Doodh Plus hamare certified idaray **Allah Ho Traders** (Bahria Town, Lahore) ka official registered product hai."
        matched_intents.append(("brand", reply))

    if not matched_intents:
        return "FALLBACK / UNCLEAR VOICE APOLOGY"

    selected = matched_intents[:3]
    print(f"Detected {len(selected)} intent(s): {[k for k, _ in selected]}")
    return "\n\n".join(r for _, r in selected)

test_queries = [
    ("Voice Note 1 (Benefits + Price - 2 questions)", "میں نے اس وائس میں کہا ہے کہ مجھے اس کے فائدے بتاؤ اور اس کی پرائز بھی ساتھ بتاؤ اس کے فائدے بھی ساتھ بتاؤ کے فائ"),
    ("Voice Note 2 (Order - 1 question)", "اچھا میں یہ کیسے ارڈر کر سکتا ہوں"),
    ("Voice Note 3 (Price - 1 question)", "اور مجھے اس کی پرائز بھی بتا"),
    ("Voice Note 4 (Brand - 1 question)", "اچھا اس کے اپ کی برانڈ کا نام کیا ہے"),
    ("Voice Note 5 (Bakri Milk - 1 question)", "اچھا بکری کا جو دودھ ہوتا ہے وہ کیسے بڑھا سکتے"),
    ("Voice Note 6 (Bhains Milk - 1 question)", "اچھا دودھ پلس سے جو میری بھینس ہے وہ کم دودھ دیتی ہے اس کا دودھ کیسے"),
    ("Voice Note 7 (Price + Order - 2 questions)", "فیز دودھ کی جو پرائز ہے وہ مجھے بتاؤ وہ کیا ہے اور میں اس کو کیسے ارڈر کر سکتا ہوں"),
    ("Voice Note 8 (Delivery Days - 1 question)", "اچھا اس کی ڈلیوری تو تفریح کے کتنے دن تک میرے گھر ا جائے"),
    ("Voice Note 9 (Delivery Days - 1 question)", "میں نے کہا یہ کتنے دن تک میرے پاس اجائے گا"),
    ("Voice Note 10 (Delivery Days - 1 question)", "میں یہ کہہ رہا ہوں کہ یہ پارسل میرے تک میرے پاس کب تک ا جائیگا کتنے دنوں میں پہنچ"),
    ("3 Questions Test (Benefits + Price + Order)", "Doodh Plus ke faiday kya hain, iska rate kya hai aur order kaise hoga?"),
    ("Price + Delivery Timeline (2 questions)", "Price kya hai aur parcel kitne din mein pohnchega?")
]

print("=" * 70)
print("TESTING MULTI-INTENT RESOLUTION")
print("=" * 70)
for label, q in test_queries:
    print(f"\n--- {label} ---")
    print(f"Query: {q}")
    res = classify_and_answer(q)
    print(f"Response:\n{res}")
