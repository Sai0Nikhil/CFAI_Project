"""
core/llm_provider.py
====================
Abstract LLM provider for multilingual hospital intent parsing.
Currently supports: Claude (Anthropic)
Pluggable: add a GeminiProvider class to swap providers.

Each provider takes a query and returns structured JSON:
{
    "destination_node": "Node_302_ICU_Tower" | None,
    "destination_friendly": "ICU (Bettenhaus Tower 3F)" | None,
    "urgency_level": "CRITICAL" | "HIGH" | "NORMAL",
    "urgency_keywords": [...],
    "language": "te" | "hi" | "en",
    "language_label": "Telugu 🇮🇳" | ...,
    "explanation": "brief reasoning",
    "raw_llm_output": "..."  # for debugging
}
"""

from __future__ import annotations
import json
import re
import os
from typing import Optional

# ---------------------------------------------------------------------------
# Hospital schema — tells the LLM what destinations exist
# ---------------------------------------------------------------------------
DESTINATIONS = [
    ("Node_302_ICU_Tower",   "ICU / Intensive Care",           "Bettenhaus Tower, Floor 3"),
    ("ENTRANCE_MAIN",        "Main Entrance / Emergency",      "Ground Floor"),
    ("Lab_101",              "Laboratory 101",                 "Historic Wing, Floor 1"),
    ("Lab_102",              "Laboratory 102",                 "Historic Wing, Floor 1"),
    ("Ward_Cardio_F7",       "Cardiology Ward",                "Bettenhaus Tower, Floor 7"),
    ("Ward_Maternity_F10",   "Maternity Ward",                 "Bettenhaus Tower, Floor 10"),
    ("Ward_Neuro_F5",        "Neurology Ward",                 "Bettenhaus Tower, Floor 5"),
    ("Ward_Oncology_F15",    "Oncology Ward",                  "Bettenhaus Tower, Floor 15"),
    ("HW_Radiology",         "Radiology / X-ray / MRI",        "Historic Wing, Floor 1"),
    ("HW_Pharmacy",          "Pharmacy",                       "Historic Wing, Ground"),
    ("Operating_F2",         "Operating Theatre / Surgery",    "Bettenhaus Tower, Floor 2"),
    ("BH_Reception",         "Reception / Front Desk",         "Bettenhaus Tower, Ground"),
]

SYSTEM_PROMPT = """You are a hospital navigation assistant for Charité Campus Mitte, Berlin.
You speak Telugu, Hindi, and English.

Given a patient query, extract:
1. **destination_node** — the most relevant node ID from the list below (or null if unclear)
2. **destination_friendly** — human-readable name
3. **urgency_level** — CRITICAL (life-threatening: bleeding, unconscious, heart attack), 
   HIGH (significant distress: severe pain, difficulty breathing), NORMAL (routine query)
4. **urgency_keywords** — list of any distress signals you detected
5. **language** — te (Telugu), hi (Hindi), en (English)
6. **explanation** — one-sentence reasoning

Valid destinations:
""" + "\n".join(f"- {nid}: {name} ({loc})" for nid, name, loc in DESTINATIONS) + """

Respond with VALID JSON only (no markdown, no code fences):
{"destination_node": "...", "destination_friendly": "...", "urgency_level": "...", "urgency_keywords": [...], "language": "...", "explanation": "..."}
"""


# ---------------------------------------------------------------------------
# Base class
# ---------------------------------------------------------------------------

class LLMProvider:
    """Abstract base for LLM providers. All methods return the same dict shape."""

    def name(self) -> str:
        raise NotImplementedError

    def parse(self, text: str) -> dict:
        raise NotImplementedError


# ---------------------------------------------------------------------------
# Claude (Anthropic)
# ---------------------------------------------------------------------------

class ClaudeProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "claude-3-haiku-20240307", timeout: int = 15):
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    def name(self) -> str:
        return f"Claude ({self.model.split('-')[1].title()})"

    def parse(self, text: str) -> dict:
        try:
            import anthropic
        except ImportError:
            return self._fallback("anthropic SDK not installed")

        try:
            client = anthropic.Anthropic(api_key=self.api_key)
            resp = client.messages.create(
                model=self.model,
                max_tokens=300,
                temperature=0.1,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": text}],
                timeout=self.timeout,
            )
            raw = resp.content[0].text
        except Exception as e:
            return self._fallback(str(e))

        return self._parse_json(raw)

    def _parse_json(self, raw: str) -> dict:
        """Extract JSON from LLM response (handles backticks, stray text)."""
        # Try to find a JSON block
        json_match = re.search(r'\{[^{}]*\}', raw, re.DOTALL)
        if json_match:
            raw = json_match.group()

        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return self._fallback(f"Could not parse LLM output: {raw[:200]}")

        # Validate and shape into standard format
        return {
            "destination_node": data.get("destination_node") or None,
            "destination_friendly": data.get("destination_friendly") or None,
            "urgency_level": data.get("urgency_level", "NORMAL"),
            "urgency_keywords": data.get("urgency_keywords", []),
            "language": data.get("language", "en"),
            "explanation": data.get("explanation", ""),
            "raw_llm_output": raw,
            "provider": self.name(),
        }

    def _fallback(self, reason: str) -> dict:
        return {
            "destination_node": None,
            "destination_friendly": None,
            "urgency_level": "NORMAL",
            "urgency_keywords": [],
            "language": "en",
            "explanation": f"LLM unavailable: {reason}",
            "raw_llm_output": "",
            "provider": f"{self.name()} (error)",
            "error": reason,
        }


# ---------------------------------------------------------------------------
# Gemini (Google)
# ---------------------------------------------------------------------------

class GeminiProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "gemini-1.5-flash", timeout: int = 20):
        self.api_key = api_key
        self.model   = model
        self.timeout = timeout

    def name(self) -> str:
        return f"Gemini ({self.model})"

    def parse(self, text: str) -> dict:
        try:
            import google.generativeai as genai
        except ImportError:
            return self._fallback(
                "google-generativeai not installed. Run: pip install google-generativeai"
            )
        try:
            genai.configure(api_key=self.api_key)
            gmodel = genai.GenerativeModel(
                self.model,
                system_instruction=SYSTEM_PROMPT,
            )
            resp = gmodel.generate_content(
                text,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=300,
                    temperature=0.1,
                ),
            )
            raw = resp.text
        except Exception as e:
            return self._fallback(str(e))

        return self._parse_json(raw)

    def _parse_json(self, raw: str) -> dict:
        json_match = re.search(r'\{[^{}]*\}', raw, re.DOTALL)
        if json_match:
            raw = json_match.group()
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return self._fallback(f"Could not parse Gemini output: {raw[:200]}")
        return {
            "destination_node":     data.get("destination_node") or None,
            "destination_friendly": data.get("destination_friendly") or None,
            "urgency_level":        data.get("urgency_level", "NORMAL"),
            "urgency_keywords":     data.get("urgency_keywords", []),
            "language":             data.get("language", "en"),
            "explanation":          data.get("explanation", ""),
            "raw_llm_output":       raw,
            "provider":             self.name(),
        }

    def _fallback(self, reason: str) -> dict:
        return {
            "destination_node": None, "destination_friendly": None,
            "urgency_level": "NORMAL", "urgency_keywords": [],
            "language": "en",
            "explanation": f"Gemini unavailable: {reason}",
            "raw_llm_output": "", "provider": f"{self.name()} (error)",
            "error": reason,
        }


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def create_provider(provider_type: str = "claude", api_key: str = "", **kwargs) -> LLMProvider:
    """
    Factory: returns an LLMProvider instance.
    provider_type: "claude"  → ClaudeProvider (Anthropic)
                   "gemini"  → GeminiProvider (Google)
    """
    provider_type = provider_type.lower().strip()

    if provider_type == "claude":
        return ClaudeProvider(api_key, **kwargs)
    elif provider_type == "gemini":
        return GeminiProvider(api_key, **kwargs)
    else:
        raise ValueError(f"Unknown provider: '{provider_type}'. Supported: claude, gemini")


# ---------------------------------------------------------------------------
# Quick test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        print("Set ANTHROPIC_API_KEY env var to test")
        sys.exit(1)

    provider = create_provider("claude", api_key)
    for q in [
        "ICU ki le jao jaldi",
        "నాకు గుండె నొప్పి వస్తోంది సహాయం",
        "Where is the pharmacy?",
        "आईसीयू ले जाओ",
    ]:
        result = provider.parse(q)
        print(f"\nQ: {q}")
        print(f"  → {result['destination_node'] or '❓'} | {result['urgency_level']} | {result['language']}")
        print(f"  Explanation: {result['explanation']}")
