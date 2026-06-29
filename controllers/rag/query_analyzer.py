"""Lightweight query analysis helpers for ECU chatbot retrieval."""

from __future__ import annotations

import re


_WORD_RE = re.compile(r"[\w\u0600-\u06ff]+", re.UNICODE)
_ARABIC_RE = re.compile(r"[\u0600-\u06ff]")
_LATIN_RE = re.compile(r"[A-Za-z]")
_MOJIBAKE_ARABIC_RE = re.compile(r"[Ã˜Ã™]")
_ARABIC_DIACRITICS_RE = re.compile(r"[\u064b-\u065f\u0670]")

_STOPWORDS = {
    "a",
    "about",
    "an",
    "and",
    "are",
    "available",
    "can",
    "do",
    "does",
    "for",
    "have",
    "has",
    "how",
    "i",
    "in",
    "is",
    "it",
    "me",
    "more",
    "of",
    "on",
    "please",
    "tell",
    "the",
    "there",
    "to",
    "what",
    "where",
    "who",
    "with",
    "\u0627\u0644\u0649",
    "\u0625\u0644\u0649",
    "\u0627\u0646",
    "\u0623\u0646",
    "\u0627\u0648",
    "\u0623\u0648",
    "\u0627\u064a\u0647",
    "\u0623\u064a\u0647",
    "\u0627\u064a\u0646",
    "\u0623\u064a\u0646",
    "\u0628\u0647\u0627",
    "\u0628\u0647",
    "\u0641\u064a",
    "\u0644\u064a",
    "\u0645\u0627",
    "\u0645\u0639",
    "\u0645\u0646",
    "\u0647\u0644",
    "\u0647\u064a",
    "\u0647\u0648",
    "\u0639\u0646",
}

_INTENT_KEYWORDS = {
    "faculty_info": {
        "faculty",
        "faculties",
        "college",
        "colleges",
        "department",
        "departments",
        "dean",
        "\u0643\u0644\u064a\u0629",
        "\u0643\u0644\u064a\u0627\u062a",
        "\u0627\u0644\u0643\u0644\u064a\u0627\u062a",
        "\u0642\u0633\u0645",
        "\u0627\u0642\u0633\u0627\u0645",
        "\u0623\u0642\u0633\u0627\u0645",
        "\u0639\u0645\u064a\u062f",
    },
    "professor_info": {
        "professor",
        "professors",
        "doctor",
        "doctors",
        "staff",
        "instructor",
        "office",
        "\u062f\u0643\u062a\u0648\u0631",
        "\u062f\u0643\u0627\u062a\u0631\u0629",
        "\u0627\u0633\u062a\u0627\u0630",
        "\u0623\u0633\u062a\u0627\u0630",
        "\u0627\u0633\u0627\u062a\u0630\u0629",
        "\u0623\u0633\u0627\u062a\u0630\u0629",
        "\u0645\u0643\u062a\u0628",
    },
    "room_location": {
        "room",
        "rooms",
        "where",
        "location",
        "located",
        "building",
        "floor",
        "cafeteria",
        "hall",
        "lab",
        "\u0627\u064a\u0646",
        "\u0623\u064a\u0646",
        "\u0645\u0643\u0627\u0646",
        "\u0645\u0648\u0642\u0639",
        "\u0642\u0627\u0639\u0629",
        "\u0642\u0627\u0639\u0627\u062a",
        "\u0645\u0628\u0646\u0649",
        "\u062f\u0648\u0631",
        "\u0643\u0627\u0641\u064a\u062a\u0631\u064a\u0627",
    },
    "course_schedule": {
        "course",
        "courses",
        "class",
        "classes",
        "schedule",
        "time",
        "semester",
        "\u0645\u0642\u0631\u0631",
        "\u0645\u0642\u0631\u0631\u0627\u062a",
        "\u0645\u0627\u062f\u0629",
        "\u062c\u062f\u0648\u0644",
        "\u0645\u0648\u0639\u062f",
        "\u0645\u062d\u0627\u0636\u0631\u0629",
    },
    "event_info": {
        "event",
        "events",
        "activity",
        "activities",
        "news",
        "open",
        "\u0641\u0639\u0627\u0644\u064a\u0629",
        "\u0641\u0639\u0627\u0644\u064a\u0627\u062a",
        "\u0646\u0634\u0627\u0637",
        "\u0627\u062e\u0628\u0627\u0631",
        "\u0623\u062e\u0628\u0627\u0631",
    },
    "admission_info": {
        "admission",
        "admissions",
        "apply",
        "application",
        "requirements",
        "fees",
        "tuition",
        "\u0642\u0628\u0648\u0644",
        "\u0627\u0644\u0642\u0628\u0648\u0644",
        "\u062a\u0642\u062f\u064a\u0645",
        "\u0645\u0635\u0627\u0631\u064a\u0641",
        "\u0631\u0633\u0648\u0645",
        "\u0634\u0631\u0648\u0637",
    },
    "general_info": {
        "ecu",
        "university",
        "campus",
        "services",
        "help",
        "\u0627\u0644\u062c\u0627\u0645\u0639\u0629",
        "\u062c\u0627\u0645\u0639\u0629",
        "\u062e\u062f\u0645\u0627\u062a",
        "\u0645\u0633\u0627\u0639\u062f\u0629",
    },
}


def detect_language(text: str) -> str:
    """Detect Arabic, English, or mixed Arabic/English text."""
    has_arabic = bool(_ARABIC_RE.search(text))
    has_mojibake_arabic = bool(_MOJIBAKE_ARABIC_RE.search(text))
    has_latin = bool(_LATIN_RE.search(text))
    if has_mojibake_arabic:
        return "mixed" if has_latin and any(char.isascii() for char in text if char.isalpha()) else "ar"
    if has_arabic and has_latin:
        return "mixed"
    if has_arabic:
        return "ar"
    return "en"


def normalize_query(text: str) -> str:
    """Normalize query text for deterministic Arabic/English matching."""
    normalized = text.casefold().strip()
    normalized = _ARABIC_DIACRITICS_RE.sub("", normalized)
    replacements = {
        "\u0623": "\u0627",
        "\u0625": "\u0627",
        "\u0622": "\u0627",
        "\u0649": "\u064a",
        "\u0629": "\u0647",
        "\u0624": "\u0648",
        "\u0626": "\u064a",
    }
    for old, new in replacements.items():
        normalized = normalized.replace(old, new)
    return " ".join(_WORD_RE.findall(normalized))


def extract_keywords(text: str) -> list[str]:
    """Extract useful normalized keywords while preserving first-seen order."""
    keywords: list[str] = []
    seen: set[str] = set()
    for token in _WORD_RE.findall(normalize_query(text)):
        token = token.strip("_?\u061f.,\u060c:;!()[]{}")
        token = _simple_stem(token)
        if not token or token in _STOPWORDS or len(token) <= 1:
            continue
        if token.startswith("\u0627\u0644") and len(token) > 3:
            token = token[2:]
        if token not in seen:
            seen.add(token)
            keywords.append(token)
    return keywords


def detect_intent(text: str) -> str:
    """Detect the most likely university information intent."""
    keywords = set(extract_keywords(text))
    if not keywords:
        return "unknown"

    best_intent = "unknown"
    best_score = 0
    for intent, terms in _INTENT_KEYWORDS.items():
        normalized_terms = {_simple_stem(term) for term in terms}
        score = len(keywords & normalized_terms)
        if score > best_score:
            best_intent = intent
            best_score = score
    return best_intent if best_score > 0 else "unknown"


def _simple_stem(token: str) -> str:
    """Handle small spelling/case differences without heavy NLP dependencies."""
    if token.endswith("ies") and len(token) > 4:
        return f"{token[:-3]}y"
    if token.endswith("s") and len(token) > 4 and not any("\u0600" <= char <= "\u06ff" for char in token):
        return token[:-1]
    return token
