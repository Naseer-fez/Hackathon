"""Multilingual query processor and translator for Indic procurement terms."""
from __future__ import annotations

import re
import unicodedata

# Common Indic procurement terms mapped to standard English technical terms
INDIC_TERM_MAP: dict[str, str] = {
    # Hindi
    "सौर": "solar photovoltaic", "सोलर": "solar photovoltaic", "फोटोवोल्टिक": "photovoltaic solar module",
    "पैनल": "pv module panel", "इनवर्टर": "inverter power converter", "सरिया": "tmt steel rebar reinforcement",
    "टीएमटी": "tmt steel rebar fe 500d", "सीमेंट": "ordinary portland cement", "तार": "pvc insulated electric wire",
    "केबल": "cable wire", "स्ट्रीट लाइट": "led street light", "अग्निशामक": "fire extinguisher",
    "आग": "fire extinguisher", "पाइप": "hdpe pipe", "हेलमेट": "safety helmet", "ट्रांसफार्मर": "distribution transformer",
    # Tamil
    "சூரிய": "solar photovoltaic", "மின்மாற்றி": "distribution transformer", "கம்பி": "steel rebar",
    "தீயணைப்பான்": "fire extinguisher", "சிமெண்ட்": "portland cement",
    # Telugu
    "సౌర": "solar photovoltaic", "ట్రాన్స్‌ఫార్మర్": "distribution transformer", "సిమెంట్": "cement",
    # Bengali
    "সৌর": "solar photovoltaic", "প্যানেল": "pv module panel", "ট্রান্সফরমার": "distribution transformer",
    "অগ্নি": "fire extinguisher", "নির্বাপক": "fire extinguisher", "রড": "tmt steel rebar",
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
        expanded_parts: list[str] = []

        for indic_term, english_equiv in INDIC_TERM_MAP.items():
            if indic_term in text or indic_term in cleaned:
                expanded_parts.append(english_equiv)

        if not expanded_parts:
            expanded_parts = [text]
        else:
            expanded_parts.append(text)

        translated = " ".join(dict.fromkeys(expanded_parts))
        return translated, script
