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
    # ICU
    (["icu", "intensive care", "critical care",
      "ఐసీయూ", "ఐ సి యు", "icu కి", "critical",
      "आईसीयू", "गहन चिकित्सा", "icu le jao", "icu ki", "icu jaana",
      "bettenhaus icu", "node_302", "node 302"],
     "Node_302_ICU_Tower", "ICU (Bettenhaus Tower)"),

    # Emergency / Entrance
    (["emergency", "urgent", "accident", "help me", "please help",
      "అత్యవసర", "సహాయం", "emergency ki", "emergency jaana",
      "आपातकालीन", "मदद करो", "मदद", "emergency le jao"],
     "ENTRANCE_MAIN", "Emergency Entrance"),

    # Lab
    (["lab", "laboratory", "blood test", "sample",
      "లాబ్", "lab ki", "lab jaana", "laboratory ki",
      "प्रयोगशाला", "लैब", "lab le jao", "lab 101"],
     "Lab_101", "Laboratory 101 (Historic Wing)"),

    # Cardiology
    (["cardiology", "heart", "cardiac", "cardiologist",
      "గుండె", "heart ki", "cardiology ki",
      "हृदय", "कार्डियोलॉजी", "heart le jao"],
     "Ward_Cardio_F7", "Cardiology Ward (Floor 7)"),

    # Maternity
    (["maternity", "delivery", "obstetrics", "gynecology", "gynaecology",
      "ప్రసూతి", "delivery ki", "maternity ki",
      "प्रसूति", "डिलीवरी", "maternity le jao"],
     "Ward_Maternity_F10", "Maternity Ward (Floor 10)"),

    # Neurology
    (["neurology", "neuro", "brain", "neurosurgeon",
      "న్యూరో", "brain ki", "neuro ki",
      "न्यूरोलॉजी", "दिमाग", "neuro le jao"],
     "Ward_Neuro_F5", "Neurology Ward (Floor 5)"),

    # Oncology
    (["oncology", "cancer", "tumor", "tumour",
      "కాన్సర్", "cancer ki", "oncology ki",
      "ऑन्कोलॉजी", "कैंसर", "cancer le jao"],
     "Ward_Oncology_F15", "Oncology Ward (Floor 15)"),

    # Radiology
    (["radiology", "x-ray", "xray", "mri", "ct scan", "scan",
      "రేడియాలజీ", "xray ki", "radiology ki",
      "रेडियोलॉजी", "एक्स-रे", "mri le jao"],
     "HW_Radiology", "Radiology (Historic Wing)"),

    # Pharmacy
    (["pharmacy", "medicine", "drugs", "pharmacist",
      "ఫార్మసీ", "medicine ki", "pharmacy ki",
      "फार्मेसी", "दवाई", "pharmacy le jao"],
     "HW_Pharmacy", "Pharmacy (Historic Wing)"),

    # Operating theatre
    (["operating", "operation", "surgery", "theatre", "theater",
      "ఆపరేషన్", "surgery ki", "operation ki",
      "ऑपरेशन", "सर्जरी", "surgery le jao"],
     "Operating_F2", "Operating Theatre (Floor 2)"),

    # General ward / reception
    (["reception", "front desk", "registration", "register",
      "రిసెప్షన్", "reception ki",
      "स्वागत", "रिसेप्शन", "reception le jao"],
     "BH_Reception", "Reception (Bettenhaus)"),

    # Entrance / exit
    (["entrance", "exit", "main gate", "front entrance",
      "ప్రవేశ ద్వారం", "entrance ki",
      "प्रवेश", "मुख्य द्वार", "entrance le jao"],
     "ENTRANCE_MAIN", "Main Entrance"),
]

# ────────────────────────────────────────────────────────────────────────────
# Urgency / Distress keyword detection
# ────────────────────────────────────────────────────────────────────────────

URGENCY_KEYWORDS = {
    # English
    "emergency", "urgent", "hurry", "fast", "quickly", "dying",
    "unconscious", "bleeding", "heart attack", "stroke", "pain",
    "can't breathe", "not breathing", "collapse", "faint", "help",
    "please help", "sos", "critical",
    # Telugu
    "అత్యవసర", "వేగంగా", "సహాయం", "నొప్పి", "గుండె నొప్పి",
    "స్పృహ కోల్పోయారు", "రక్తస్రావం",
    # Hindi
    "आपातकालीन", "जल्दी", "मदद", "दर्द", "बेहोश",
    "खून", "सांस नहीं", "दिल का दौरा",
    # Roman transliteration hints
    "emergency hai", "jaldi", "madad karo", "help karo",
    "noppi", "sahaayam",
}

CALM_INDICATORS = {"okay", "fine", "please", "thank you", "thanks", "धन्यवाद", "ధన్యవాదాలు"}


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

    O(K) K=urgency keyword count
    """
    text_lower = text.lower()
    matched = [kw for kw in URGENCY_KEYWORDS if kw.lower() in text_lower]
    calm_matched = [kw for kw in CALM_INDICATORS if kw.lower() in text_lower]

    if len(matched) >= 2:
        level = "CRITICAL"
        emoji = "🚨"
        routing_hint = "URGENT — trigger emergency routing, alert ward staff"
    elif len(matched) == 1:
        level = "HIGH"
        emoji = "⚠️"
        routing_hint = "Elevated urgency — prioritise elevator access"
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
        "matched_keywords": matched,
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

    intent = extract_intent(raw_text)
    urgency = detect_urgency(raw_text)

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

    target_node = intent[0] if intent else None
    target_friendly = intent[1] if intent else None

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
    """Return selected model string from session state."""
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
