"""
IRS Forms normalization utilities

Implements docs/irs-forms/README.md section "1) Normalization rules" in Python
for use by the AI service / data ingestion pipelines.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Dict
import re


# Language and territory codes from docs/irs-forms/forms-schema.yaml
LANGUAGE_CODES = {
    "en",
    "sp",
    "ko",
    "ru",
    "vie",
    "zh-s",
    "zh-t",
    "ht",
    "ja",
    "fr",
    "de",
    "it",
    "pl",
    "pt",
    "ar",
    "bn",
    "fa",
    "guj",
    "km",
    "pa",
    "so",
    "tl",
    "ur",
}

TERRITORY_CODES = {"US", "PR", "VI", "GU", "AS", "CNMI"}


@dataclass
class CanonicalForm:
    """
    Canonical representation of an IRS form.

    Examples:
      - "Form W-4 (sp)" -> canonical_id="W-4", language="sp"
      - "Form 1040 (Schedule C) (sp)" -> canonical_id="1040 Schedule C",
        language="sp", is_schedule=True, schedule_code="C"
    """

    canonical_id: str
    raw_title: str
    document_kind: str  # "form", "instructions", "publication", "notice", "other"
    language: str = "en"
    territory: str = "US"
    is_schedule: bool = False
    schedule_code: Optional[str] = None


FORM_PREFIX_RE = re.compile(r"^Form\s+", re.IGNORECASE)
PUBLICATION_PREFIX_RE = re.compile(r"^Publication\b", re.IGNORECASE)
INSTRUCTION_PREFIX_RE = re.compile(r"^Instructions?\b", re.IGNORECASE)
NOTICE_PREFIX_RE = re.compile(r"^Notice\b", re.IGNORECASE)


def is_form_row(title: str) -> bool:
    """
    Returns True if this row should be treated as a "Form …" row per the README.

    - Keeps only rows whose title starts with "Form "
    - Drops anything starting with Publication / Instruction / Notice
    """
    trimmed = title.strip()

    if (
        PUBLICATION_PREFIX_RE.match(trimmed)
        or INSTRUCTION_PREFIX_RE.match(trimmed)
        or NOTICE_PREFIX_RE.match(trimmed)
    ):
        return False

    return FORM_PREFIX_RE.match(trimmed) is not None


def _parse_parentheticals(title_without_prefix: str) -> Dict[str, Optional[str]]:
    result: Dict[str, Optional[str]] = {"language": None, "territory": None, "schedule_code": None}

    for match in re.finditer(r"\(([^)]+)\)", title_without_prefix):
        value = match.group(1).strip()

        # Schedule markers like "Schedule C", "Schedule 1-A"
        sched = re.fullmatch(r"Schedule\s+([A-Za-z0-9-]+)", value, re.IGNORECASE)
        if sched:
            result["schedule_code"] = sched.group(1)
            continue

        upper = value.upper()
        if upper in TERRITORY_CODES:
            result["territory"] = upper
            continue

        lower = value.lower()
        if lower in LANGUAGE_CODES:
            result["language"] = lower

    return result


def normalize_form_title(raw_title: str) -> Optional[CanonicalForm]:
    """
    Normalize a "Form …" product title into a canonical record.

    Returns None for non-form rows (publications/instructions/notices).
    """
    title = raw_title.strip()

    if not is_form_row(title):
        return None

    # Strip leading "Form "
    without_prefix = FORM_PREFIX_RE.sub("", title).strip()

    # Pull metadata from parentheticals first
    parsed = _parse_parentheticals(without_prefix)
    language = parsed["language"]
    territory = parsed["territory"]
    schedule_code = parsed["schedule_code"]

    # Remove all parentheticals from the base name
    base = re.sub(r"\s*\([^)]*\)", "", without_prefix).strip()

    # If we discovered a schedule_code but "Schedule" is not in the base,
    # append it so that canonical_id matches "1040 Schedule C" pattern.
    if schedule_code and not re.search(r"Schedule\s+", base, re.IGNORECASE):
        base = f"{base} Schedule {schedule_code}"

    # Infer territory from concatenated suffix (e.g. "W-2VI") if needed
    if territory is None:
        for code in TERRITORY_CODES:
            if code == "US":
                continue
            if base.endswith(code):
                territory = code
                break

    return CanonicalForm(
        canonical_id=base,
        raw_title=raw_title,
        document_kind="form",
        language=language or "en",
        territory=territory or "US",
        is_schedule=bool(schedule_code),
        schedule_code=schedule_code,
    )

