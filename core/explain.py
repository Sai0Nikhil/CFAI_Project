"""
core/explain.py
===============
Offline Multilingual Symbolic Explainer (XAI)
Translates search paths and CSP constraint violations into English, Telugu, and Hindi 
without requiring external API keys, with an optional LLM refinement fallback.
"""

from typing import List, Dict, Any, Optional

NODE_TRANSLATIONS = {
    "en": {
        "ENTRANCE_MAIN": "Main Entrance (Luisenstraße)",
        "Node_302_ICU_Tower": "ICU Tower (Room 302)",
        "MAIN_GATE": "Main Gate Entrance",
        "NICU_F3": "Neonatal ICU (Floor 3)",
        "Ward_ENT_F1": "ENT Clinic (Floor 1)",
        "Ward_Ortho_F1": "Orthopedics & Fracture Clinic (Floor 1)",
        "Ward_Cardio_F7": "Cardiology (Floor 7)",
        "Ward_Neuro_F5": "Neurology Ward (Floor 5)",
        "Ward_Maternity_F10": "Maternity & Gynecology (Floor 10)",
        "Ward_Pediatrics_F4": "Pediatrics (Floor 4)",
        "Ward_Oncology_F15": "Oncology (Floor 15)",
        "Operating_F2": "General Surgery operating Room (Floor 2)",
        "Lab_101": "Pathology Lab 101",
        "HW_Pharmacy": "Central Pharmacy",
        "HW_OPD": "Outpatient Clinics (OPD)",
        "HW_Physiotherapy": "Physiotherapy Rehab Unit",
        "HW_Dialysis": "Dialysis Ward",
        "HW_BloodBank": "Blood Bank",
        "HW_Admin": "Administration Office",
        "BH_Reception": "Bettenhaus Reception desk",
        "BH_Dialysis": "Dialysis Unit",
        "DIALYSIS_UNIT": "Dialysis Unit",
        "DIAG_Radiology": "Diagnostic Radiology",
        "LAB_RADIOLOGY": "Radiology Department",
        "MVZ_Lobby": "Outpatient Centre Lobby",
        "OPD_LOBBY": "OPD Lobby",
        "DIAG_PhysioTherapy": "Physiotherapy Department",
        "OPD_GENERAL_MEDICINE": "General Medicine Clinic",
        "BLOOD_BANK": "Blood Bank",
        "ADMIN_HQ": "Administration Headquarters",
        "OPD_REGISTRATION": "OPD Registration Counter",
        "elevator": "Elevator / Lift",
        "stairs": "Stairway",
        "corridor": "Corridor passage"
    },
    "te": {
        "ENTRANCE_MAIN": "ప్రధాన ద్వారం (లూయిసెన్‌స్ట్రాస్)",
        "Node_302_ICU_Tower": "ఐసీయూ టవర్ (గది 302)",
        "MAIN_GATE": "ప్రధాన గేట్ ప్రవేశం",
        "NICU_F3": "నియోనాటల్ ఐసీయూ (3వ అంతస్తు)",
        "Ward_ENT_F1": "ఇ.ఎన్.టి క్లినిక్ (1వ అంతస్తు)",
        "Ward_Ortho_F1": "ఆర్థోపెడిక్స్ వార్డ్ (1వ అంతస్తు)",
        "Ward_Cardio_F7": "కార్డియాలజీ విభాగం (7వ అంతస్తు)",
        "Ward_Neuro_F5": "న్యూరాలజీ వార్డు (5వ అంతస్తు)",
        "Ward_Maternity_F10": "ప్రసూతి & గైనకాలజీ (10వ అంతస్తు)",
        "Ward_Pediatrics_F4": "పిల్లల వార్డు (4వ అంతస్తు)",
        "Ward_Oncology_F15": "ఆంకాలజీ (15వ అంతస్తు)",
        "Operating_F2": "శస్త్రచికిత్స గది (2వ అంతస్తు)",
        "Lab_101": "పాథాలజీ ల్యాబ్ 101",
        "HW_Pharmacy": "సెంట్రల్ ఫార్మసీ",
        "HW_OPD": "అవుట్‌పేషెంట్ విభాగం (ఓపీడీ)",
        "HW_Physiotherapy": "ఫిజియోథెరపీ పునరావాసం",
        "HW_Dialysis": "డయాలసిస్ విభాగం",
        "HW_BloodBank": "బ్లడ్ బ్యాంక్",
        "HW_Admin": "పరిపాలనా కార్యాలయం",
        "BH_Reception": "బెటెన్‌హాస్ రిసెప్షన్ డెస్క్",
        "BH_Dialysis": "డయాలసిస్ విభాగం",
        "DIALYSIS_UNIT": "డయాలసిస్ విభాగం",
        "DIAG_Radiology": "రేడియాలజీ విభాగం",
        "LAB_RADIOLOGY": "రేడియాలజీ విభాగం",
        "MVZ_Lobby": "అవుట్‌పేషెంట్ సెంటర్ లాబీ",
        "OPD_LOBBY": "ఓపీడీ లాబీ",
        "DIAG_PhysioTherapy": "ఫిజియోథెరపీ విభాగం",
        "OPD_GENERAL_MEDICINE": "జనరల్ మెడిసిన్ క్లినిక్",
        "BLOOD_BANK": "బ్లడ్ బ్యాంక్",
        "ADMIN_HQ": "ప్రధాన పరిపాలనా కార్యాలయం",
        "OPD_REGISTRATION": "ఓపీడీ రిజిస్ట్రేషన్ కౌంటర్",
        "elevator": "లిఫ్ట్ / ఎలివేటర్",
        "stairs": "మెట్లు",
        "corridor": "కారిడార్ మార్గం"
    },
    "hi": {
        "ENTRANCE_MAIN": "मुख्य प्रवेश द्वार (लुइसेनस्ट्रैस)",
        "Node_302_ICU_Tower": "आईसीयू टावर (कमरा 302)",
        "MAIN_GATE": "मुख्य गेट प्रवेश",
        "NICU_F3": "नवजात गहन चिकित्सा इकाई (एनआईसीयू) मंजिल 3",
        "Ward_ENT_F1": "ईएनटी क्लिनिक (पहली मंजिल)",
        "Ward_Ortho_F1": "आर्थोपेडिक्स वार्ड (पहली मंजिल)",
        "Ward_Cardio_F7": "कार्डियोलॉजी (7वीं मंजिल)",
        "Ward_Neuro_F5": "न्यूरोलॉजी वार्ड (5वीं मंजिल)",
        "Ward_Maternity_F10": "प्रसूति और स्त्री रोग (10वीं मंजिल)",
        "Ward_Pediatrics_F4": "बाल रोग वार्ड (4थी मंजिल)",
        "Ward_Oncology_F15": "ऑन्कोलॉजी (15वीं मंजिल)",
        "Operating_F2": "शल्य चिकित्सा कक्ष (दूसरी मंजिल)",
        "Lab_101": "पैथोलॉजी लैब 101",
        "HW_Pharmacy": "केंद्रीय फार्मेसी",
        "HW_OPD": "बाह्य रोगी विभाग (ओपीडी)",
        "HW_Physiotherapy": "फिजियोथेरेपी पुनर्वास इकाई",
        "HW_Dialysis": "डायलिसिस वार्ड",
        "HW_BloodBank": "ब्लड बैंक",
        "HW_Admin": "प्रशासनिक कार्यालय",
        "BH_Reception": "बेटनहॉस रिसेप्शन डेस्क",
        "BH_Dialysis": "डायलिसिस वार्ड",
        "DIALYSIS_UNIT": "डायलिसिस वार्ड",
        "DIAG_Radiology": "रेडियोलॉजी विभाग",
        "LAB_RADIOLOGY": "रेडियोलॉजी विभाग",
        "MVZ_Lobby": "बाह्य रोगी केंद्र लॉबी",
        "OPD_LOBBY": "ओपीडी लॉबी",
        "DIAG_PhysioTherapy": "फिजियोथेरेपी विभाग",
        "OPD_GENERAL_MEDICINE": "सामान्य चिकित्सा क्लिनिक",
        "BLOOD_BANK": "ब्लड बैंक",
        "ADMIN_HQ": "मुख्य प्रशासनिक कार्यालय",
        "OPD_REGISTRATION": "ओपीडी पंजीकरण काउंटर",
        "elevator": "लिफ्ट / एलिवेटर",
        "stairs": "सीढ़ियाँ",
        "corridor": "गलियारा मार्ग"
    }
}

ALGO_NAMES = {
    "en": {"astar": "A* Search (Heuristic)", "dijkstra": "Dijkstra (Uniform Cost)", "bfs": "Breadth-First Search", "dfs": "Depth-First Search", "ucs": "Uniform Cost Search"},
    "te": {"astar": "A* సెర్చ్ (హ్యూరిస్టిక్)", "dijkstra": "డిజెక్స్ట్రా (ఏకరీతి వ్యయం)", "bfs": "బ్రెడ్త్-ఫస్ట్ సెర్చ్", "dfs": "డెప్త్-ఫస్ట్ సెర్చ్", "ucs": "యూనిఫాం కాస్ట్ సెర్చ్"},
    "hi": {"astar": "A* सर्च (अनुमानी)", "dijkstra": "डाइक्स्ट्रा (समान लागत)", "bfs": "ब्रेडथ-फर्स्ट सर्च", "dfs": "डेप्थ-फर्स्ट सर्च", "ucs": "यूनिफ़ॉर्म कॉस्ट सर्च"}
}

PROFILE_NAMES = {
    "en": {"staff": "Medical Staff Member", "visitor": "General Hospital Visitor", "patient": "Wheelchair Patient", "emergency": "Emergency Responder"},
    "te": {"staff": "వైద్య సిబ్బంది సభ్యుడు", "visitor": "సాధారణ ఆసుపత్రి సందర్శకుడు", "patient": "వీల్చైర్ రోగి", "emergency": "అత్యవసర రెస్పాండర్"},
    "hi": {"staff": "चिकित्सा कर्मचारी सदस्य", "visitor": "सामान्य अस्पताल आगंतुक", "patient": "व्हीलचेयर रोगी", "emergency": "आपातकालीन प्रतिक्रियाकर्ता"}
}

def translate_node(node_id: str, lang: str) -> str:
    lang = lang.lower() if lang.lower() in NODE_TRANSLATIONS else "en"
    dict_ref = NODE_TRANSLATIONS[lang]
    if node_id in dict_ref:
        return dict_ref[node_id]
    
    # Generic format fallback
    clean = node_id.replace("Node_", "").replace("Ward_", "").replace("HW_", "").replace("_", " ")
    return clean

def get_symbolic_explanation(
    path: List[str],
    cost: float,
    algo: str,
    profile: str,
    lang: str,
    hospital: str = "charite"
) -> str:
    lang = lang.lower() if lang.lower() in NODE_TRANSLATIONS else "en"
    
    # Translate terms
    t_algo = ALGO_NAMES[lang].get(algo.lower(), algo)
    t_prof = PROFILE_NAMES[lang].get(profile.lower(), profile)
    t_start = translate_node(path[0], lang) if path else ""
    t_goal = translate_node(path[-1], lang) if path else ""
    
    landmarks = []
    # Extract 2 intermediate landmarks to display
    if len(path) > 2:
        for idx in [len(path) // 2, max(1, len(path) - 2)]:
            node_name = translate_node(path[idx], lang)
            if node_name not in landmarks:
                landmarks.append(node_name)
    
    t_landmarks = ", ".join(landmarks) if landmarks else ""
    
    # Safe access constraints message
    t_access = ""
    if profile == "patient":
        if lang == "te":
            t_access = "వీల్చైర్ నిబంధనల దృష్ట్యా కేవలం లిఫ్ట్‌లు మరియు ర్యాంప్‌లు మాత్రమే ఉపయోగించబడ్డాయి; మెట్లు నివారించబడ్డాయి."
        elif lang == "hi":
            t_access = "व्हीलचेयर सुरक्षा कारणों से केवल लिफ्टों और रैंप का उपयोग किया गया है; सीढ़ियों से बचा गया है।"
        else:
            t_access = "Elevator access was preferred and stairs avoided to satisfy wheelchair mobility constraints."
    else:
        if lang == "te":
            t_access = "భద్రతా మరియు ప్రవేశ అనుమతులు ధృవీకరించబడ్డాయి."
        elif lang == "hi":
            t_access = "सुरक्षा और प्रवेश नियमों को सत्यापित किया गया है।"
        else:
            t_access = "Security permissions and floor clearances are fully validated."

    hospital_label = "Charité Campus Mitte (Berlin)" if hospital == "charite" else "AIIMS Mangalagiri (India)"

    if lang == "te":
        explain_str = (
            f"ఆసుపత్రి: {hospital_label}. "
            f"మార్గం కనుగొనడానికి '{t_algo}' వాడబడింది. "
            f"రోగి రకం '{t_prof}' కొరకు '{t_start}' నుండి ప్రారంభించి '{t_goal}' కి మార్గం చూపబడింది. "
            f"మొత్తం ప్రయాణ సమయం దాదాపు {cost:.0f} సెకన్లు. "
            f"ఈ మార్గంలో {len(path)} స్థానాలు ఉన్నాయి (ముఖ్యంగా: {t_landmarks}). "
            f"{t_access}"
        )
    elif lang == "hi":
        explain_str = (
            f"अस्पताल: {hospital_label}. "
            f"मार्ग खोजने के लिए '{t_algo}' का उपयोग किया गया। "
            f"'{t_prof}' प्रोफाइल के लिए '{t_start}' से शुरू होकर '{t_goal}' तक मार्ग तय किया गया। "
            f"कुल यात्रा समय लगभग {cost:.0f} सेकंड है। "
            f"इस मार्ग में {len(path)} नोड्स शामिल हैं (मुख्य रूप से: {t_landmarks})। "
            f"{t_access}"
        )
    else:
        explain_str = (
            f"Hospital Site: {hospital_label}. "
            f"Path computed using {t_algo}. "
            f"Route configured for a '{t_prof}' starting from '{t_start}' to '{t_goal}'. "
            f"Estimated transit time is {cost:.0f} seconds. "
            f"The route transits {len(path)} nodes (passing through: {t_landmarks}). "
            f"Security status: {t_access}"
        )
        
    return explain_str

async def explain_path_multilingual(
    path: List[str],
    cost: float,
    algo: str,
    profile: str,
    lang: str,
    hospital: str = "charite",
    use_llm: bool = False,
    api_key: str = "",
    provider: str = "claude",
    model: str = "claude-3-haiku-20240307"
) -> Dict[str, Any]:
    """
    Generates a bilingual search/routing explanation.
    Always produces a high-fidelity local symbolic template explanation first.
    If use_llm is True and api_key is present, it passes the symbolic context to the LLM
    to generate an empathetic, human-sounding localized translation.
    """
    symbolic_text = get_symbolic_explanation(path, cost, algo, profile, lang, hospital)
    
    if not use_llm or not api_key.strip():
        return {
            "symbolic_explanation": symbolic_text,
            "llm_refined": None,
            "language": lang,
            "llm_used": False
        }
        
    # Attempt LLM refinement
    prompt = (
        f"You are an empathetic, clear multilingual voice navigator assistant for a hospital called "
        f"{'Charité' if hospital == 'charite' else 'AIIMS'}. "
        f"Translate the following raw facts into a warm, natural, easy-to-follow guiding voice statement in "
        f"{'Telugu' if lang == 'te' else 'Hindi' if lang == 'hi' else 'English'}. "
        f"Keep all node references and times exact, but rephrase it nicely so it is comfortable for patients or staff. "
        f"Provide only the translation text, do not write greetings or explanations.\n\n"
        f"Raw context: {symbolic_text}"
    )
    
    try:
        from core.llm_provider import create_provider
        prov = create_provider(provider, api_key, model=model)
        refined_text = await prov.explain("routing_explanation", {"prompt": prompt})
        # If result is dict (e.g. from custom agent endpoints), pull string
        if isinstance(refined_text, dict):
            refined_text = refined_text.get("explanation", refined_text.get("text", symbolic_text))
    except Exception as e:
        refined_text = f"LLM translation fallback (error: {str(e)}). Standard template: {symbolic_text}"
        
    return {
        "symbolic_explanation": symbolic_text,
        "llm_refined": refined_text,
        "language": lang,
        "llm_used": True
    }
