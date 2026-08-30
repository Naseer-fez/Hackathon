"""Multilingual query processor and translator for Indic procurement terms."""
from __future__ import annotations

import re
import unicodedata

# Common Indic procurement terms mapped to standard English technical terms
INDIC_TERM_MAP: dict[str, str] = {
    "सौर": "solar photovoltaic",
    "सोलर": "solar photovoltaic",
    "पैनल": "pv module panel",
    "इनवर्टर": "inverter power converter",
    "सरिया": "tmt steel rebar reinforcement",
    "सीमेंट": "ordinary portland cement",
    "तार": "pvc insulated electric wire cable",
    "केबल": "cable wire",
    "स्ट्रीट लाइट": "led street light luminaire",
    "बत्ती": "led lamp luminaire",
    "अग्निशामक": "fire extinguisher",
    "आग": "fire safety extinguisher",
    "पाइप": "hdpe pipe water supply",
    "हेलमेट": "industrial safety helmet",
    "मुखौटा": "respiratory mask particulate",
    "मास्क": "respiratory mask n95 ppe",
    "ट्रांसफार्मर": "distribution transformer",
    "स्विच": "plug socket switch",
    "कंप्यूटर": "laptop computer server",
    "बैटरी": "lithium secondary battery cell",
}


class MultilingualProcessor:
    """Detects and translates multilingual Indic queries into technical terms."""

    def detect_script(self, text: str) -> str:
        """Detect script of given query text (e.g. Devanagari, Latin)."""
        for char in text:
            name = unicodedata.name(char, "")
            if "DEVANAGARI" in name:
                return "hi"
            if "TAMIL" in name:
                return "ta"
            if "TELUGU" in name:
                return "te"
            if "BENGALI" in name:
                return "bn"
        return "en"

    def translate_and_expand(self, text: str) -> tuple[str, str]:
        """Translate Indic query into expanded English search terms."""
        script = self.detect_script(text)
        if script == "en":
            return text, "en"

        cleaned = re.sub(r"[^\w\s]", " ", text.lower())
        tokens = cleaned.split()
        expanded_parts: list[str] = [text]

        for token in tokens:
            for indic_term, english_equiv in INDIC_TERM_MAP.items():
                if indic_term in token or token in indic_term:
                    expanded_parts.append(english_equiv)

        translated = " ".join(dict.fromkeys(expanded_parts))
        return translated, script
