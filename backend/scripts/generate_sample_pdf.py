import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def generate_official_doodh_plus_pdf(output_path: str):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#065f46'),
        spaceAfter=12
    )
    heading_style = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontSize=13,
        leading=16,
        textColor=colors.HexColor('#047857'),
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True
    )
    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor('#1f2937'),
        spaceAfter=6
    )
    bullet_style = ParagraphStyle(
        'Bullet',
        parent=body_style,
        leftIndent=12,
        spaceAfter=4
    )

    story = []

    # Title & Header
    story.append(Paragraph("DOODH PLUS MINERAL MIXTURE (دوده پلس منرل مکسچر)", title_style))
    story.append(Paragraph("Brand: Allah Ho Traders (اللہ ہو ٹریڈرز) | Bahria Town, Lahore", heading_style))
    story.append(Paragraph("Official Knowledge Base & WhatsApp AI Agent Reference Document", body_style))
    story.append(Spacer(1, 10))

    # Chapter 1: Introduction & Background
    story.append(Paragraph("CHAPTER 1: INTRODUCTION & BACKGROUND (تعارف اور پس منظر)", heading_style))
    story.append(Paragraph(
        "Company: Allah Ho Traders, Bahria Town, Lahore. Product: 'Doodh Plus' (دوده پلس) Mineral Mixture & Growth Booster. "
        "Purpose: Formulated for livestock (cows, buffaloes, sheep, goats) to eliminate hidden mineral and micro-nutrient deficiencies caused by poor fodder. "
        "It acts like an essential multi-vitamin booster for animals, activating genetic potential for milk and meat without harmful chemicals, hormones, or antibiotics.",
        body_style
    ))
    story.append(Paragraph("• 100% natural, chemical-free, pure mineral formulation with zero antibiotics or cheap fillers.", bullet_style))
    story.append(Paragraph("• Dramatically increases milk yield (Quantity) and Fat & SNF quality (گاڑھا دودھ اور فیٹ).", bullet_style))
    story.append(Paragraph("• Maximizes farmer profit by reducing feed waste and enhancing animal health.", bullet_style))
    story.append(Spacer(1, 8))

    # Chapter 2: Ingredients & Scientific Formulation
    story.append(Paragraph("CHAPTER 2: INGREDIENTS & SCIENTIFIC FORMULATION (اجزاء اور ساخت)", heading_style))
    story.append(Paragraph(
        "1. Calcium & Phosphorus (کیلشیم اور فاسفورس): Balanced ratio for skeletal strength, teeth, high milk production, and prevention of milk fever (ملک فیور).\n"
        "2. Vitamins A, D3, E: Improves reproductive system, skin health, eyesight, and immunity.\n"
        "3. Trace Minerals (Zinc, Copper, Cobalt, Iodine, Manganese, Selenium): Red blood cell formation, oxygen transport, shiny coat, hoof strength, and mastitis resistance.\n"
        "4. Buffers & Probiotics (بفرز اور پروبائیوٹکس): Controls rumen acidity (معدے کی تیزابیت) and maximizes nutrient absorption so feed is not wasted in dung.",
        body_style
    ))
    story.append(Spacer(1, 8))

    # Chapter 3: Key Benefits
    story.append(Paragraph("CHAPTER 3: DETAILED SCIENTIFIC & PRACTICAL BENEFITS (تفصیلی فوائد)", heading_style))
    story.append(Paragraph("• 1. Milk Yield & Rich Quality (زیادہ اور گاڑھا دودھ): Stimulates mammary glands (تھنوں کے دودھ بنانے والے غدود), increases Fat & SNF ratio, fetches highest market rate.", bullet_style))
    story.append(Paragraph("• 2. Reproductive & Pregnancy Solutions (تولیدی صلاحیت اور گبن ہونے کے مسائل): Solves heat issues (وقت پر ہیٹ میں نہ آنا), fixes repeat breeding/failed artificial insemination (بار بار فیل ہونے والا سیمن/کراس).", bullet_style))
    story.append(Paragraph("• 3. Immunity & Stamina (صحت، طاقت اور تگڑا پن): Cures post-milking exhaustion and weakness, gives active posture, shiny skin and clean tail.", bullet_style))
    story.append(Paragraph("• 4. Mastitis Protection (ساڑو کی بیماری سے حفاظت): Builds an immune shield against udder inflammation and bacterial infections.", bullet_style))
    story.append(Paragraph("• 5. Rapid Growth Booster (بچوں، کٹوں اور بچھڑوں کی تیز نشوونما): Strengthens bone frame, rapid weight gain for meat and Qurbani.", bullet_style))
    story.append(Paragraph("• 6. Cures Pica Syndrome (مٹی، گوبر، دیواریں، کپڑے چاٹنے کی عادت کا خاتمہ): Mineral replenishment permanently ends abnormal licking habits.", bullet_style))
    story.append(Paragraph("• 7. Easy Placenta Expulsion (جیر کا آسانی سے اخراج): Facilitates quick, clean expulsion of placenta after calving, protecting against infections.", bullet_style))
    story.append(Paragraph("• 8. Better Digestion & Feed Absorption (پیٹ کی صفائی اور ہاضمہ): Feeds beneficial gut bacteria; converts every particle of fodder into body power and milk.", bullet_style))
    story.append(Spacer(1, 8))

    # Chapter 4: Dosage & Feeding Guidelines
    story.append(PageBreak())
    story.append(Paragraph("CHAPTER 4: DOSAGE & FEEDING GUIDELINES (خوراک اور استعمال کا طریقہ)", heading_style))
    
    dosage_table = [
        ["Animal Category", "Recommended Daily Dosage", "Method of Feeding"],
        ["Large Animals (گائے، بھینس، اونٹ، گھوڑا)", "Half Cup (~100 grams daily)", "Mix in morning or evening wanda, dalia, khal, or moist fodder."],
        ["Small Animals (بکری، بھیڑ، چھوٹے بچھڑے، کٹے)", "2 Tablespoons (20 - 30 grams daily)", "Mix well into daily feed or wanda."]
    ]
    t_dosage = Table(dosage_table, colWidths=[150, 160, 220])
    t_dosage.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#ecfdf5')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor('#065f46')),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 6),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#d1d5db')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
    ]))
    story.append(t_dosage)
    story.append(Spacer(1, 10))

    # Chapter 5: Packaging, Pricing & Economic Value
    story.append(Paragraph("CHAPTER 5: PACKAGING & PRICING (پیکنگ اور قیمتیں)", heading_style))
    pricing_table = [
        ["Pack Size", "Weight", "Official Price", "Recommended For"],
        ["Small Pack (چھوٹا پیک)", "1 KG", "1,750 RS", "Small households with 1 or 2 animals."],
        ["Big Pack (بڑا پیک)", "10 KG", "12,500 RS", "Commercial dairy farms & multiple animals (Big savings pack)."]
    ]
    t_price = Table(pricing_table, colWidths=[120, 70, 100, 240])
    t_price.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#eff6ff')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor('#1e40af')),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 6),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#d1d5db')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
    ]))
    story.append(t_price)
    story.append(Spacer(1, 10))

    # Chapter 6: Golden Rule of Full Course
    story.append(Paragraph("CHAPTER 6: GOLDEN RULE OF FULL COURSE (کورس کا سنہری اصول)", heading_style))
    story.append(Paragraph(
        "Do not stop after a single 1kg pack. Stopping prematurely gives only temporary relief, and the animal may revert to weakness. "
        "A full course (preferably 10kg pack or continuous feeding) is necessary for long-term health and maximum profit.",
        body_style
    ))
    story.append(Spacer(1, 8))

    # Chapter 7: Ordering & Facilities
    story.append(Paragraph("CHAPTER 7: ORDERING & DELIVERY TERMS (آرڈر اور ترسیل کی سہولیات)", heading_style))
    story.append(Paragraph("• Free Home Delivery (فری ہوم ڈیلیوری): Delivered to doorsteps across all Pakistan with NO extra delivery charges.", bullet_style))
    story.append(Paragraph("• Cash on Delivery (COD - کیش آن ڈیلیوری): Pay money only when parcel arrives in your hands.", bullet_style))
    story.append(Paragraph("• Official Contact Numbers (رابطہ نمبرز): 0333-9697189 | 0325-9694309", bullet_style))
    story.append(Paragraph("• How to Order (آرڈر کا طریقہ): Send your Name, Complete Address, and Phone Number via WhatsApp to book immediately.", bullet_style))
    story.append(Spacer(1, 8))

    # Chapter 8: Frequently Asked Questions (FAQs)
    story.append(Paragraph("CHAPTER 8: FREQUENTLY ASKED QUESTIONS (FAQS - اکثر پوچھے جانے والے سوالات)", heading_style))
    story.append(Paragraph("<b>Q1: کیا یہ حاملہ جانوروں کے لیے محفوظ ہے؟ (Is it safe for pregnant animals?)</b><br/>"
                           "جواب: جی ہاں! دوده پلس حاملہ جانوروں کے لیے انتہائی مفید ہے، کیونکہ یہ پیٹ میں پلنے والے بچے کی ہڈیوں اور نشوونما میں مدد کرتا ہے اور ماں کو کمزوری سے بچاتا ہے۔", body_style))
    story.append(Paragraph("<b>Q2: اس کا اثر کتنے دنوں میں نظر آتا ہے؟ (When do results show?)</b><br/>"
                           "جواب: 7 سے 10 دنوں میں جانور کی چمک، پھرتی اور ہاضمے میں واضح بہتری نظر آتی ہے، جبکہ دودھ کی مقدار میں اضافہ 10 سے 15 دنوں میں نمایاں ہو جاتا ہے۔", body_style))
    story.append(Paragraph("<b>Q3: کیا اسے گرمیوں اور سردیوں دونوں میں دیا جا سکتا ہے؟ (Can it be used in summer & winter?)</b><br/>"
                           "جواب: بالکل! یہ تمام موسموں کے لیے یکساں مفید ہے۔ گرمیوں میں لو اور تھکن سے بچاتا ہے اور سردیوں میں توانائی کی کمی پوری کرتا ہے۔", body_style))

    doc.build(story)
    print(f"Official Doodh Plus PDF generated at {output_path}")

if __name__ == "__main__":
    generate_official_doodh_plus_pdf("c:/Users/surface/OneDrive/Desktop/DHOOD PLUS WATSAPP CHATBOT/backend/storage/documents/Dhoodh_Plus_Official_Knowledge_Base.pdf")
