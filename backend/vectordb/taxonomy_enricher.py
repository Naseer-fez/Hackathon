"""Taxonomy and Indic ontology enricher for Indian Standards embeddings."""
from __future__ import annotations

import sys
from typing import Any
from backend.vectordb.config import vector_db_settings


class TaxonomyEnricher:
    """Enriches standard chunks with domain abbreviations, trade slang, and Indic terms."""

    def __init__(self, source_repo_path: str | None = None) -> None:
        repo_path = source_repo_path or vector_db_settings.source_repo_path
        if repo_path not in sys.path:
            sys.path.insert(0, repo_path)
        try:
            from src.taxonomy.normalizer import TaxonomyNormalizer
            from src.taxonomy.indic_dictionary import IndicDictionary
            self.external_taxonomy_available = True
        except (ImportError, ModuleNotFoundError):
            TaxonomyNormalizer = None
            IndicDictionary = None
            self.external_taxonomy_available = False

        self._normalizer = TaxonomyNormalizer() if self.external_taxonomy_available else None
        self._indic_dict = IndicDictionary() if self.external_taxonomy_available else None

    def get_abbreviations_for_text(self, text: str) -> list[str]:
        """Find matching domain abbreviations in text and return expansions."""
        if not self.external_taxonomy_available:
            return []
        text_upper = text.upper()
        found: list[str] = []
        for abbr, model in self._normalizer._abbreviations.items():
            if f" {abbr} " in f" {text_upper} " or f"({abbr})" in text_upper:
                found.append(f"{abbr} ({model.full_name} - {model.domain_category})")
        return found

    def get_trade_terms_for_standard(self, is_number: str) -> list[str]:
        """Find colloquial trade terms mapped to this standard."""
        if not self.external_taxonomy_available:
            return []
        norm_is = is_number.upper().strip()
        matched: list[str] = []
        for trade_key, item in self._normalizer._trade_terms.items():
            if item.standard_id.upper().startswith(norm_is) or norm_is.startswith(item.standard_id.upper()):
                matched.append(f"{item.trade_term} -> {item.formal_term}")
        return matched

    def get_indic_terms_for_standard(self, is_number: str) -> dict[str, Any]:
        """Fetch 10-language translations, transliterations, and slang for standard."""
        if not self.external_taxonomy_available:
            return {"scripts": {}, "transliterations": {}, "slang": [], "synonyms": []}
        entry = self._indic_dict._entries_by_std.get(is_number)
        if not entry:
            for k, v in self._indic_dict._entries_by_std.items():
                if is_number.split(":")[0].strip().upper() == k.split(":")[0].strip().upper():
                    entry = v
                    break
        if not entry:
            return {"scripts": {}, "transliterations": {}, "slang": [], "synonyms": []}
        return {
            "scripts": dict(entry.script_translations),
            "transliterations": dict(entry.transliterations),
            "slang": list(entry.colloquial_slang),
            "synonyms": list(entry.synonyms),
        }

    def build_taxonomy_injection_block(self, is_number: str, text: str) -> str:
        """Construct formatted taxonomy injection block to append to embedding chunk."""
        abbrs = self.get_abbreviations_for_text(text)
        trade_terms = self.get_trade_terms_for_standard(is_number)
        indic = self.get_indic_terms_for_standard(is_number)

        lines: list[str] = ["[DOMAIN TAXONOMY & SYNONYMS]"]
        if abbrs:
            lines.append(f"• Technical Acronyms: {'; '.join(abbrs)}")
        if trade_terms:
            lines.append(f"• Trade & Tender Jargon: {'; '.join(trade_terms)}")
        if indic["synonyms"]:
            lines.append(f"• Domain Synonyms: {', '.join(indic['synonyms'])}")
        if indic["slang"]:
            lines.append(f"• Colloquial Slang: {', '.join(indic['slang'])}")
        if indic["scripts"]:
            script_str = " | ".join(f"{lang}: {val}" for lang, val in indic["scripts"].items())
            lines.append(f"• Multilingual Indic: {script_str}")
        if indic["transliterations"]:
            translit_str = " | ".join(f"{lang}: {val}" for lang, val in indic["transliterations"].items())
            lines.append(f"• Phonetic Transliterations: {translit_str}")

        return "\n".join(lines) if len(lines) > 1 else ""
