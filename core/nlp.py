"""
core/nlp.py
===========
CO6 / NLP Pipeline — Multilingual Hospital Navigation Intent Parser
Languages: Telugu (తెలుగు) · Hindi (हिंदी) · English
+ Roman transliteration of Telugu & Hindi
+ Urgency / Distress Emotion Detection
+ Optional LLM-enhanced parsing (Claude / Gemini — pluggable)

Pipeline (rule-based):
  1. Language detection  (langdetect or heuristic fallback)
  2. Transliteration normalisation (indic-transliteration if available)
  3. Keyword-based intent extraction → target node
  4. Urgency/emotion detection → URGENT flag
  5. Return structured parse result for downstream routing

LLM-enhanced mode (when configured):
  → Calls LLM provider for intent + urgency extraction
  → Falls back to rule-based on error or timeout

Complexity: O(L * K) per query  L=query_length, K=keyword_count
"""

from __future__ import annotations
import re
import os
from typing import Optional

# ────────────────────────────────────────────────────────────────────────────
# Optional library imports (graceful fallback)
# ────────────────────────────────────────────────────────────────────────────

try:
    from langdetect import detect as _ld_detect
    _LANGDETECT_OK = True
except ImportError:
    _LANGDETECT_OK = False

try:
    from indic_transliteration import sanscript
    from indic_transliteration.sanscript import transliterate as _itr
    _INDIC_OK = True
except ImportError:
    _INDIC_OK = False


# ────────────────────────────────────────────────────────────────────────────
# Keyword → node mappings  (all three languages + Roman forms)
# ────────────────────────────────────────────────────────────────────────────

# Each entry: (keywords_list, target_node, friendly_name)
INTENT_MAP = [

    # ── ICU / NICU ───────────────────────────────────────────────────────────
    (["icu", "intensive care", "critical care", "ventilator",
      "ఐసీయూ", "ఐ సి యు", "icu కి", "critical", "nicu",
      "आईसीयू", "गहन चिकित्सा", "icu le jao", "icu ki", "icu jaana"],
     "Node_302_ICU_Tower", "ICU — Intensive Care Unit"),

    # ── EMERGENCY ────────────────────────────────────────────────────────────
    (["emergency", "emergency room", "er", "casualty", "accident",
      "అత్యవసర", "అపాయం", "emergency ki", "emergency jaana",
      "आपातकालीन", "इमरजेंसी", "emergency le jao", "er le jao"],
     "ENTRANCE_MAIN", "Emergency (ER) — Main Entrance"),

    # ── ENT — symptoms & department name ────────────────────────────────────
    (["ent", "ear", "nose", "throat", "hearing", "ear pain", "ear ache",
      "ear infection", "tonsil", "tonsils", "sinus", "sinusitis",
      "sneezing", "runny nose", "blocked nose", "nasal", "nosebleed",
      "hoarse", "hoarseness", "voice problem", "swallowing problem",
      "కన్", "చెవి", "చెవి నొప్పి", "ముక్కు", "గొంతు", "సైనస్",
      "ear ki", "ent ki", "throat ki", "nose ki",
      "कान", "कान दर्द", "नाक", "गला", "टॉन्सिल", "साइनस",
      "kan mein dard", "ent le jao", "ear le jao"],
     "Ward_ENT_F1", "ENT — Ear, Nose & Throat · Floor 1"),

    # ── ORTHOPEDICS — symptoms & department name ─────────────────────────────
    (["orthopedics", "ortho", "orthopedic", "bone", "fracture", "broken bone",
      "joint pain", "knee pain", "back pain", "spine", "shoulder pain",
      "hip", "ligament", "tendon", "sprain", "cast", "plaster",
      "arthritis", "slip disc", "slipped disc", "wrist pain", "ankle",
      "ఎముక", "ఎముక విరిగింది", "మోకాలు నొప్పి", "వెన్ను నొప్పి",
      "bone ki", "ortho ki", "fracture ki",
      "हड्डी", "फ्रैक्चर", "घुटना दर्द", "कमर दर्द", "जोड़ दर्द",
      "haddi ki", "ortho le jao", "fracture le jao"],
     "Ward_Ortho_F1", "Orthopedics & Fracture Clinic · Floor 1"),

    # ── CARDIOLOGY — symptoms & department name ──────────────────────────────
    (["cardiology", "heart", "cardiac", "cardiologist", "chest pain",
      "palpitation", "heart attack", "angina", "ecg", "echo",
      "high bp", "blood pressure", "hypertension", "heart failure",
      "గుండె", "గుండె నొప్పి", "గుండె పోటు", "heart ki", "cardiology ki",
      "हृदय", "दिल", "सीने में दर्द", "दिल का दौरा", "कार्डियोलॉजी",
      "dil ki", "heart le jao", "chest pain le jao"],
     "Ward_Cardio_F7", "Cardiology · Floor 7"),

    # ── NEUROLOGY — symptoms & department name ───────────────────────────────
    (["neurology", "neuro", "brain", "neurosurgeon", "neurologist",
      "headache", "migraine", "seizure", "epilepsy", "stroke",
      "paralysis", "memory loss", "dementia", "tremor", "parkinson",
      "తల నొప్పి", "పక్షవాతం", "న్యూరో", "brain ki", "neuro ki",
      "सिरदर्द", "माइग्रेन", "लकवा", "न्यूरोलॉजी", "दिमाग",
      "neuro le jao", "brain le jao", "headache ki"],
     "Ward_Neuro_F5", "Neurology · Floor 5"),

    # ── MATERNITY & OBSTETRICS / GYNAECOLOGY ────────────────────────────────
    (["maternity", "delivery", "obstetrics", "gynecology", "gynaecology",
      "pregnant", "pregnancy", "labour", "labor", "antenatal", "prenatal",
      "cesarean", "c-section", "gynaecologist", "gynecologist",
      # Vaginal / menstrual / women's health symptoms
      "vagina", "vaginal", "vaginal bleeding", "bleeding in vagina",
      "heavy bleeding", "heavy bleding", "heavy bledding",
      "menstrual", "menstruation", "periods", "period pain", "period",
      "irregular periods", "missed period", "uterus", "ovary", "ovarian",
      "pcos", "pcod", "endometriosis", "fibroid", "pelvic pain",
      "white discharge", "discharge", "vulva", "cervix",
      # Telugu
      "ప్రసూతి", "గర్భం", "గర్భస్రావం", "రుతుక్రమం", "యోని",
      "delivery ki", "maternity ki",
      # Hindi
      "प्रसूति", "गर्भावस्था", "डिलीवरी", "प्रसव", "स्त्री रोग",
      "योनि", "माहवारी", "पीरियड", "गर्भाशय", "महिला रोग",
      "delivery le jao", "maternity le jao", "gynecology le jao"],
     "Ward_Maternity_F10", "Maternity & Obstetrics · Floor 10"),

    # ── PEDIATRICS ───────────────────────────────────────────────────────────
    (["pediatrics", "pediatric", "paediatrics", "child", "children",
      "baby", "infant", "newborn", "kids ward", "child doctor",
      "పిల్లల వైద్యం", "పిల్లలు", "baby ki", "child ki",
      "बच्चा", "शिशु", "बाल रोग", "नवजात",
      "baby le jao", "child le jao", "pediatrics le jao"],
     "Ward_Pediatrics_F4", "Pediatrics & Child Care · Floor 4"),

    # ── ONCOLOGY ─────────────────────────────────────────────────────────────
    (["oncology", "cancer", "tumor", "tumour", "chemotherapy", "chemo",
      "radiation therapy", "radiotherapy", "biopsy", "lymphoma",
      "కాన్సర్", "అర్బుదం", "cancer ki", "oncology ki",
      "ऑन्कोलॉजी", "कैंसर", "कीमोथेरेपी",
      "cancer le jao", "chemo le jao"],
     "Ward_Oncology_F15", "Oncology & Chemotherapy · Floor 15"),

    # ── GENERAL SURGERY ──────────────────────────────────────────────────────
    (["surgery", "operation", "operating", "theatre", "theater", "ot",
      "surgical", "appendix", "hernia", "gallbladder", "gallstone",
      "laparoscopy", "appendectomy",
      "ఆపరేషన్", "శస్త్రచికిత్స", "surgery ki", "operation ki",
      "ऑपरेशन", "सर्जरी", "शल्य चिकित्सा",
      "surgery le jao", "operation le jao"],
     "Operating_F2", "General Surgery OT · Floor 2"),

    # ── RADIOLOGY ────────────────────────────────────────────────────────────
    (["radiology", "x-ray", "xray", "mri", "ct scan", "scan",
      "ultrasound", "sonography", "mammogram", "imaging",
      "రేడియాలజీ", "ఎక్స్-రే", "xray ki", "mri ki", "scan ki",
      "रेडियोलॉजी", "एक्स-रे", "एमआरआई", "अल्ट्रासाउंड",
      "xray le jao", "mri le jao", "scan le jao"],
     "HW_Radiology", "Radiology — X-Ray & MRI"),

    # ── PATHOLOGY LAB ────────────────────────────────────────────────────────
    (["lab", "laboratory", "blood test", "sample", "pathology",
      "urine test", "culture", "biopsy report", "haemogram", "cbc",
      "లాబ్", "రక్త పరీక్ష", "lab ki", "blood test ki",
      "प्रयोगशाला", "लैब", "खून जांच", "पैथोलॉजी",
      "lab le jao", "blood test le jao"],
     "Lab_101", "Pathology Lab"),

    # ── PHARMACY ─────────────────────────────────────────────────────────────
    (["pharmacy", "medicine", "drugs", "pharmacist", "tablets", "pills",
      "prescription", "medication", "chemist",
      "ఫార్మసీ", "మందులు", "medicine ki", "pharmacy ki",
      "फार्मेसी", "दवाई", "दवाखाना", "दवा",
      "pharmacy le jao", "medicine le jao", "dawai le jao"],
     "HW_Pharmacy", "Central Pharmacy"),

    # ── OPD ──────────────────────────────────────────────────────────────────
    (["opd", "outpatient", "out patient", "consultation", "doctor appointment",
      "general doctor", "physician", "general physician", "checkup", "check up",
      "ఓపీడీ", "వైద్యుడు", "opd ki", "doctor ki",
      "ओपीडी", "बाह्य रोगी", "डॉक्टर",
      "opd le jao", "doctor le jao"],
     "HW_OPD", "Outpatient Department (OPD)"),

    # ── PHYSIOTHERAPY ────────────────────────────────────────────────────────
    (["physiotherapy", "physio", "rehabilitation", "rehab",
      "exercise therapy", "physical therapy", "massage therapy",
      "ఫిజియోథెరపీ", "పునరావాసం", "physio ki",
      "फिजियोथेरेपी", "पुनर्वास",
      "physio le jao", "rehab le jao"],
     "HW_Physiotherapy", "Physiotherapy & Rehabilitation"),

    # ── DIALYSIS ─────────────────────────────────────────────────────────────
    (["dialysis", "kidney", "renal", "kidney failure", "hemodialysis",
      "మూత్రపిండాలు", "కిడ్నీ", "dialysis ki", "kidney ki",
      "डायलिसिस", "किडनी", "वृक्क",
      "dialysis le jao", "kidney le jao"],
     "HW_Dialysis", "Dialysis Unit"),

    # ── BLOOD BANK ───────────────────────────────────────────────────────────
    (["blood bank", "blood donation", "transfusion", "blood group",
      "donate blood", "blood supply",
      "రక్త బ్యాంకు", "రక్తదానం", "blood bank ki",
      "ब्लड बैंक", "रक्त दान", "रक्त भंडार",
      "blood bank le jao", "blood le jao"],
     "HW_BloodBank", "Blood Bank"),

    # ── ADMINISTRATION / RECORDS ─────────────────────────────────────────────
    (["admin", "administration", "medical records", "records", "certificate",
      "discharge summary", "billing", "bill payment", "insurance",
      "రికార్డులు", "నిర్వహణ", "admin ki", "records ki",
      "प्रशासन", "रिकॉर्ड", "बिल", "बिलिंग",
      "admin le jao", "records le jao"],
     "HW_Admin", "Administration & Medical Records"),

    # ── RECEPTION / REGISTRATION ─────────────────────────────────────────────
    (["reception", "front desk", "registration", "register",
      "రిసెప్షన్", "నమోదు", "reception ki",
      "स्वागत", "रजिस्ट्रेशन", "रिसेप्शन",
      "reception le jao"],
     "BH_Reception", "Reception & Registration"),

    # ── ENTRANCE ─────────────────────────────────────────────────────────────
    (["entrance", "exit", "main gate", "front entrance", "main door",
      "ప్రవేశ ద్వారం", "entrance ki",
      "प्रवेश द्वार", "मुख्य द्वार",
      "entrance le jao"],
     "ENTRANCE_MAIN", "Main Entrance · Luisenstraße"),
]

# ────────────────────────────────────────────────────────────────────────────
# Urgency / Distress keyword detection
# ────────────────────────────────────────────────────────────────────────────

URGENCY_KEYWORDS = {
    # English — general
    "emergency", "urgent", "hurry", "fast", "quickly", "dying",
    "unconscious", "bleeding", "bleding", "bledding",   # typo variants
    "heavy bleeding", "heavy bleding", "heavy bledding",
    "heart attack", "stroke", "pain", "severe pain", "intense pain",
    "can't breathe", "cannot breathe", "not breathing", "difficulty breathing",
    "collapse", "collapsed", "faint", "fainted", "fainting",
    "help", "please help", "sos", "critical", "serious",
    "accident", "injury", "injured", "wound", "trauma",
    "overdose", "poisoning", "seizure", "convulsion",
    "chest pain", "vomiting blood", "blood in urine", "high fever",
    "vaginal bleeding",   # women's health emergency
    # Telugu
    "అత్యవసర", "వేగంగా", "సహాయం", "నొప్పి", "గుండె నొప్పి",
    "స్పృహ కోల్పోయారు", "రక్తస్రావం", "రక్తం పోతోంది",
    # Hindi
    "आपातकालीन", "जल्दी", "मदद", "दर्द", "बेहोश",
    "खून", "खून बह रहा", "सांस नहीं", "दिल का दौरा",
    "तेज दर्द", "बहुत दर्द",
    # Roman transliteration
    "emergency hai", "jaldi", "madad karo", "help karo",
    "noppi", "sahaayam", "bahut dard", "khoon aa raha",
}

# Single keyword = always CRITICAL (no need for 2 matches)
CRITICAL_KEYWORDS = {
    "heavy bleeding", "heavy bleding", "heavy bledding",
    "vaginal bleeding", "bleeding in vagina",
    "heart attack", "cardiac arrest",
    "can't breathe", "cannot breathe", "not breathing",
    "unconscious", "not responding",
    "vomiting blood", "blood in stool", "blood in urine",
    "seizure", "convulsion", "overdose", "poisoning",
    "dying", "dying now", "stroke", "collapse", "collapsed",
    "గుండె నొప్పి",   # Telugu: chest pain
    "రక్తస్రావం",     # Telugu: hemorrhage
    "दिल का दौरा",    # Hindi: heart attack
    "खून बह रहा",     # Hindi: blood is flowing
    "सांस नहीं",      # Hindi: not breathing
}

CALM_INDICATORS = {"okay", "fine", "please", "thank you", "thanks", "धन्यवाद", "ధన్యవాదాలు"}

# ── Irrelevant / non-medical query detection ─────────────────────────────────
IRRELEVANT_KEYWORDS = {
    # Weather / general knowledge
    "weather", "temperature", "rain", "sunny", "forecast", "climate",
    # Food / restaurants
    "food", "restaurant", "hungry", "eat", "lunch", "dinner", "breakfast",
    "pizza", "burger", "coffee", "tea", "water",
    # Sports / entertainment
    "cricket", "football", "movie", "film", "song", "music", "game",
    "ipl", "match", "score", "tv", "netflix",
    # Tech / random
    "phone", "mobile", "internet", "wifi", "computer", "laptop", "app",
    "google", "youtube", "instagram", "facebook", "whatsapp",
    # Greetings with no medical context
    "hello", "hi", "hey", "good morning", "good night", "how are you",
    "what is your name", "who are you", "tell me a joke",
    # Academics / other
    "homework", "exam", "college", "school", "university", "study",
    # Telugu irrelevant
    "వాతావరణం", "సినిమా", "ఆహారం", "క్రికెట్",
    # Hindi irrelevant
    "मौसम", "खाना", "फिल्म", "क्रिकेट",
}

# Medical anchor words — if ANY of these appear, it's definitely medical
MEDICAL_ANCHORS = {
    "doctor", "hospital", "ward", "pain", "ache", "hurt", "bleeding",
    "blood", "fever", "medicine", "tablet", "injection", "surgery",
    "icu", "opd", "lab", "scan", "mri", "xray", "pharmacy", "nurse",
    "patient", "treatment", "diagnosis", "symptom", "disease", "illness",
    # Telugu
    "నొప్పి", "వైద్యుడు", "ఆసుపత్రి", "రక్తం", "జ్వరం", "మందులు",
    # Hindi
    "दर्द", "डॉक्टर", "अस्पताल", "खून", "बुखार", "दवाई",
}


# ────────────────────────────────────────────────────────────────────────────
# Language detection
# ────────────────────────────────────────────────────────────────────────────

def detect_language(text: str) -> str:
    """
    Detect language of the input text.
    Returns: 'te' (Telugu) | 'hi' (Hindi) | 'en' (English) | 'unknown'

    Uses langdetect if available, otherwise heuristic Unicode-range check.
    O(text_length)
    """
    # Heuristic: check Unicode ranges first (fast, no library needed)
    telugu_chars = sum(1 for c in text if 'ఀ' <= c <= '౿')
    devanagari_chars = sum(1 for c in text if 'ऀ' <= c <= 'ॿ')

    if telugu_chars > 2:
        return "te"
    if devanagari_chars > 2:
        return "hi"

    # Fall back to langdetect
    if _LANGDETECT_OK:
        try:
            lang = _ld_detect(text)
            if lang in ("te", "hi", "en"):
                return lang
            return "en"  # default to English for Roman text
        except Exception:
            return "en"

    return "en"  # safe default


# ────────────────────────────────────────────────────────────────────────────
# Intent extraction
# ────────────────────────────────────────────────────────────────────────────

def extract_intent(text: str) -> Optional[tuple[str, str]]:
    """
    Match text against INTENT_MAP keywords.
    Returns (node_id, friendly_name) or None.

    O(K * L) K=number of keyword entries, L=text length
    """
    text_lower = text.lower().strip()
    best_match = None
    best_score = 0

    for keywords, node_id, friendly in INTENT_MAP:
        for kw in keywords:
            if kw.lower() in text_lower:
                # Longer keyword match = better specificity
                if len(kw) > best_score:
                    best_score = len(kw)
                    best_match = (node_id, friendly)

    return best_match


# ────────────────────────────────────────────────────────────────────────────
# Urgency / emotion detection
# ────────────────────────────────────────────────────────────────────────────

def detect_urgency(text: str) -> dict:
    """
    Scan for urgency/distress signals.
    Returns urgency level: 'CRITICAL' | 'HIGH' | 'NORMAL'

    Rules:
      - Any CRITICAL_KEYWORDS match → always CRITICAL (single match sufficient)
      - 2+ URGENCY_KEYWORDS matches → CRITICAL
      - 1 URGENCY_KEYWORDS match → HIGH
      - Otherwise → NORMAL

    O(K) K=keyword count
    """
    text_lower = text.lower()

    # Check CRITICAL_KEYWORDS first — single match is enough
    critical_matched = [kw for kw in CRITICAL_KEYWORDS if kw.lower() in text_lower]
    matched = [kw for kw in URGENCY_KEYWORDS if kw.lower() in text_lower]
    calm_matched = [kw for kw in CALM_INDICATORS if kw.lower() in text_lower]

    if critical_matched or len(matched) >= 2:
        level = "CRITICAL"
        emoji = "🚨"
        routing_hint = "URGENT — emergency routing activated, alerting ward staff"
    elif len(matched) == 1:
        level = "HIGH"
        emoji = "⚠️"
        routing_hint = "Elevated urgency — prioritising elevator access"
    elif calm_matched:
        level = "NORMAL"
        emoji = "😊"
        routing_hint = "Standard routing"
    else:
        level = "NORMAL"
        emoji = "🙂"
        routing_hint = "Standard routing"

    return {
        "level": level,
        "emoji": emoji,
        "matched_keywords": critical_matched + matched,
        "routing_hint": routing_hint,
    }


# ────────────────────────────────────────────────────────────────────────────
# Full pipeline
# ────────────────────────────────────────────────────────────────────────────

def parse_query(raw_text: str) -> dict:
    """
    Full NLP pipeline: language detect → intent extract → urgency detect.

    Returns structured result consumed by the Streamlit NLP page.

    O(L * K)  L=text length, K=keyword count
    """
    lang = detect_language(raw_text)
    lang_labels = {"te": "Telugu 🇮🇳", "hi": "Hindi 🇮🇳", "en": "English 🌐", "unknown": "Unknown"}
    lang_label = lang_labels.get(lang, lang)

    intent  = extract_intent(raw_text)
    urgency = detect_urgency(raw_text)

    # ── Relevance check ───────────────────────────────────────────────────────
    # If no intent matched AND no urgency signal AND query is long enough to be real text,
    # mark as not_relevant so the UI can show a friendly message.
    not_relevant = (
        intent is None
        and urgency["level"] == "NORMAL"
        and len(raw_text.strip()) > 3
        and not any(
            kw in raw_text.lower()
            for kw in ["hospital", "doctor", "ward", "floor", "building", "department",
                       "where", "take me", "go to", "find", "need", "want",
                       "నాకు", "నాకు కావాలి", "le jao", "jana", "chahiye",
                       "ఎక్కడ", "తీసుకు", "कहाँ", "जाना"]
        )
    )

    pipeline_steps = [
        {
            "stage": "1. Language Detection",
            "input": raw_text[:60] + ("..." if len(raw_text) > 60 else ""),
            "output": lang_label,
            "method": "Unicode range check + langdetect" if _LANGDETECT_OK else "Unicode range heuristic",
            "note": f"Detected: {lang_label}",
        },
        {
            "stage": "2. Intent Extraction",
            "input": raw_text.lower()[:60],
            "output": f"{intent[1]} → {intent[0]}" if intent else "No match",
            "method": "Keyword matching across EN/TE/HI + Roman transliteration",
            "note": (
                f"Target node: {intent[0]}" if intent
                else "❓ Could not extract destination — please rephrase"
            ),
        },
        {
            "stage": "3. Emotion / Urgency Detection",
            "input": raw_text[:60],
            "output": f"{urgency['emoji']} {urgency['level']}",
            "method": "Keyword scan across 3 languages",
            "note": urgency["routing_hint"],
        },
    ]

    target_node     = intent[0] if intent else None
    target_friendly = intent[1] if intent else None

    # ── Relevance check ───────────────────────────────────────────────────────
    text_lower = raw_text.lower()
    has_medical_anchor = any(kw in text_lower for kw in MEDICAL_ANCHORS)
    has_irrelevant     = any(kw in text_lower for kw in IRRELEVANT_KEYWORDS)
    is_irrelevant = (
        not target_node                   # no department matched
        and urgency["level"] == "NORMAL"  # not urgent
        and not has_medical_anchor        # no medical words at all
        and (has_irrelevant or len(raw_text.strip()) < 3)  # obviously off-topic or too short
    )

    if is_irrelevant:
        return {
            "raw_text": raw_text,
            "language": lang,
            "language_label": lang_label,
            "target_node": None,
            "target_friendly": None,
            "urgency": urgency,
            "pipeline_steps": pipeline_steps,
            "ready_for_routing": False,
            "llm_used": False,
            "llm_provider": None,
            "is_irrelevant": True,
            "summary": "❓ Query does not appear to be a medical navigation request.",
        }

    # Override target if urgency=CRITICAL and no intent found
    if urgency["level"] == "CRITICAL" and not target_node:
        target_node = "ENTRANCE_MAIN"
        target_friendly = "Emergency Entrance (auto-routed)"
        pipeline_steps.append({
            "stage": "4. Urgency Override",
            "input": "No intent + CRITICAL urgency",
            "output": "→ ENTRANCE_MAIN",
            "method": "Rule-based override",
            "note": "Critical urgency with no specific destination → route to main emergency entrance",
        })

    return {
        "raw_text": raw_text,
        "language": lang,
        "language_label": lang_label,
        "target_node": target_node,
        "target_friendly": target_friendly,
        "urgency": urgency,
        "pipeline_steps": pipeline_steps,
        "ready_for_routing": target_node is not None,
        "is_irrelevant": not_relevant,
        "llm_used": False,
        "llm_provider": None,
        "summary": (
            f"{urgency['emoji']} [{urgency['level']}] "
            f"Language: {lang_label} | "
            f"Destination: {target_friendly or 'Unknown'} ({target_node or 'N/A'})"
        ),
    }


# ═══════════════════════════════════════════════════════════════════════════
# LLM-Enhanced Parsing  (optional — falls back to rule-based)
# ═══════════════════════════════════════════════════════════════════════════

def get_llm_provider_type() -> str:
    """Return active provider type: 'claude' or 'gemini'."""
    # Env var set by FastAPI before calling parse_query_enhanced
    env_prov = os.environ.get("LLM_PROVIDER", "").strip()
    if env_prov in ("claude", "gemini"):
        return env_prov
    try:
        import streamlit as st
        return st.session_state.get("llm_provider", "claude")
    except (ImportError, RuntimeError):
        pass
    return "claude"


def is_llm_configured() -> bool:
    """
    True if an API key exists for the currently-selected provider.
    Checks session state first, then environment variables.
    Only relevant to NLP/speech — graph search never calls this.
    """
    try:
        import streamlit as st
        prov = get_llm_provider_type()
        key_map = {"claude": "claude_api_key", "gemini": "gemini_api_key"}
        key_field = key_map.get(prov, "claude_api_key")
        if st.session_state.get(key_field, "").strip():
            return True
    except (ImportError, RuntimeError):
        pass
    # Env-var fallback
    return bool(
        os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("GEMINI_API_KEY")
    )


def get_llm_api_key() -> str:
    """Return API key for the active provider."""
    try:
        import streamlit as st
        prov = get_llm_provider_type()
        key_map = {"claude": "claude_api_key", "gemini": "gemini_api_key"}
        key = st.session_state.get(key_map.get(prov, "claude_api_key"), "").strip()
        if key:
            return key
    except (ImportError, RuntimeError):
        pass
    return (
        os.environ.get("ANTHROPIC_API_KEY")
        or os.environ.get("GEMINI_API_KEY")
        or ""
    )


def get_llm_model() -> str:
    """Return selected model string."""
    env_model = os.environ.get("LLM_MODEL", "").strip()
    if env_model:
        return env_model
    try:
        import streamlit as st
        return st.session_state.get("llm_model", "claude-3-haiku-20240307")
    except (ImportError, RuntimeError):
        return "claude-3-haiku-20240307"


def parse_query_enhanced(raw_text: str, use_llm: bool = True) -> dict:
    """
    Parse query using LLM (if configured), with rule-based fallback.

    Args:
        raw_text: The user's spoken/typed query.
        use_llm: If True and LLM is configured, try LLM first.

    Returns:
        Same dict shape as parse_query(), with extra 'llm_used' flag.
    """
    if not use_llm or not is_llm_configured():
        result = parse_query(raw_text)
        result["llm_used"] = False
        result["llm_provider"] = None
        return result

    # Try LLM
    api_key       = get_llm_api_key()
    model         = get_llm_model()
    provider_type = get_llm_provider_type()   # "claude" | "gemini"

    try:
        from core.llm_provider import create_provider
        provider   = create_provider(provider_type, api_key, model=model)
        llm_result = provider.parse(raw_text)
    except Exception as exc:
        # LLM failed — fall back to rule-based
        result = parse_query(raw_text)
        result["llm_used"] = False
        result["llm_provider"] = None
        result["llm_error"] = str(exc)
        return result

    # LLM succeeded — merge with rule-based for completeness
    lang = llm_result.get("language") or detect_language(raw_text)
    lang_labels = {"te": "Telugu 🇮🇳", "hi": "Hindi 🇮🇳", "en": "English 🌐"}
    lang_label = lang_labels.get(lang, lang)

    urgency_level = llm_result.get("urgency_level", "NORMAL")
    matched_kw = llm_result.get("urgency_keywords", [])

    # Build urgency dict
    from copy import deepcopy
    urgency_base = detect_urgency(raw_text)  # get the full shape
    urgency_base["level"] = urgency_level
    urgency_base["matched_keywords"] = matched_kw or urgency_base["matched_keywords"]
    if urgency_level == "CRITICAL":
        urgency_base["emoji"] = "🚨"
        urgency_base["routing_hint"] = "URGENT — emergency routing (LLM detected)"
    elif urgency_level == "HIGH":
        urgency_base["emoji"] = "⚠️"
        urgency_base["routing_hint"] = "Elevated urgency (LLM detected)"
    else:
        urgency_base["routing_hint"] = f"Standard routing (LLM: {llm_result.get('explanation', '')})"

    target_node = llm_result.get("destination_node")
    target_friendly = llm_result.get("destination_friendly")

    # Build pipeline steps
    pipeline_steps = [
        {
            "stage": "1. Language Detection (LLM)",
            "input": raw_text[:60] + ("..." if len(raw_text) > 60 else ""),
            "output": lang_label,
            "method": f"LLM ({llm_result.get('provider', 'AI')})",
            "note": llm_result.get("explanation", ""),
        },
        {
            "stage": "2. Intent Extraction (LLM)",
            "input": raw_text.lower()[:60],
            "output": f"{target_friendly or '❓ Unknown'} → {target_node or 'N/A'}",
            "method": "LLM semantic understanding",
            "note": (
                f"LLM extracted: {target_node}"
                if target_node
                else "❓ Could not extract destination"
            ),
        },
        {
            "stage": "3. Urgency Detection (LLM)",
            "input": raw_text[:60],
            "output": f"{urgency_base['emoji']} {urgency_level}",
            "method": "LLM contextual analysis",
            "note": urgency_base["routing_hint"],
        },
    ]

    # Urgency override fallback
    if urgency_level == "CRITICAL" and not target_node:
        target_node = "ENTRANCE_MAIN"
        target_friendly = "Emergency Entrance (auto-routed)"
        pipeline_steps.append({
            "stage": "4. Urgency Override (LLM)",
            "input": "CRITICAL urgency + no destination",
            "output": "→ ENTRANCE_MAIN",
            "method": "Rule-based override after LLM",
            "note": "Critical distress without specific destination → route to emergency",
        })

    return {
        "raw_text": raw_text,
        "language": lang,
        "language_label": lang_label,
        "target_node": target_node,
        "target_friendly": target_friendly,
        "urgency": urgency_base,
        "pipeline_steps": pipeline_steps,
        "ready_for_routing": target_node is not None,
        "llm_used": True,
        "llm_provider": llm_result.get("provider", "Claude"),
        "llm_explanation": llm_result.get("explanation", ""),
        "summary": (
            f"{urgency_base['emoji']} [{urgency_level}] "
            f"🤖 LLM · Language: {lang_label} | "
            f"Destination: {target_friendly or 'Unknown'} ({target_node or 'N/A'})"
        ),
    }


# ═══════════════════════════════════════════════════════════════════════════
# Demo / test
# ═══════════════════════════════════════════════════════════════════════════

DEMO_QUERIES = [
    "Take me to the Bettenhaus ICU please",
    "ICU కి తీసుకెళ్ళండి",
    "आईसीयू ले जाओ जल्दी",
    "My father is bleeding! emergency help",
    "lab ki jaana hai mujhe",
    "నాకు గుండె నొప్పి వస్తోంది సహాయం",
    "Where is the pharmacy?",
    "Cardiology ward please",
]

if __name__ == "__main__":
    for q in DEMO_QUERIES:
        r = parse_query(q)
        print(f"\nQ: {q}")
        print(f"   {r['summary']}")
