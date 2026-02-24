import re
from typing import Optional


PHI_PATTERN = re.compile(r"\[\*\*[^\]]*\*\*\]")
HORIZONTAL_WHITESPACE = re.compile(r"[^\S\n]+")
MULTIPLE_NEWLINES = re.compile(r"\n{3,}")


def handle_phi_tokens(text: str, replacement: str = "[PHI]") -> str:
    return PHI_PATTERN.sub(replacement, text)


def normalize_whitespace(text: str) -> str:
    text = HORIZONTAL_WHITESPACE.sub(" ", text)
    text = MULTIPLE_NEWLINES.sub("\n\n", text)
    return text.strip()


def remove_special_characters(text: str) -> str:
    text = re.sub(r"[^\w\s\.\,\;\:\!\?\-\(\)\[\]]", " ", text)
    return text


def lowercase(text: str) -> str:
    return text.lower()


def normalize_clinical_text(
    text: str,
    handle_phi: bool = True,
    phi_replacement: str = "[PHI]",
    do_lowercase: bool = False,
    remove_special: bool = False,
) -> str:
    if handle_phi:
        text = handle_phi_tokens(text, phi_replacement)

    text = normalize_whitespace(text)

    if remove_special:
        text = remove_special_characters(text)

    if do_lowercase:
        text = lowercase(text)

    return text


def extract_sections(text: str) -> dict[str, str]:
    section_headers = [
        "CHIEF COMPLAINT",
        "HISTORY OF PRESENT ILLNESS",
        "PAST MEDICAL HISTORY",
        "MEDICATIONS",
        "ALLERGIES",
        "SOCIAL HISTORY",
        "FAMILY HISTORY",
        "PHYSICAL EXAM",
        "PERTINENT RESULTS",
        "BRIEF HOSPITAL COURSE",
        "DISCHARGE MEDICATIONS",
        "DISCHARGE DIAGNOSIS",
        "DISCHARGE CONDITION",
        "DISCHARGE INSTRUCTIONS",
        "FOLLOWUP INSTRUCTIONS",
    ]

    pattern = r"(?i)(" + "|".join(re.escape(h) for h in section_headers) + r")[\s:]*"

    sections: dict[str, str] = {}
    matches = list(re.finditer(pattern, text))

    for i, match in enumerate(matches):
        header = match.group(1).upper()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        content = text[start:end].strip()
        sections[header] = content

    return sections


def get_section_text(text: str, section_name: str) -> Optional[str]:
    sections = extract_sections(text)
    return sections.get(section_name.upper())


def truncate_text(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars]
