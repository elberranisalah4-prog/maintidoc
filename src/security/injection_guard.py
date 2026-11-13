"""Prompt Injection & Adversarial Guard Module.

Detects and neutralizes prompt injections across user queries,
OCR extracted texts, and MCP tool responses.
"""

import re
from typing import Tuple, List

# Signatures for direct and indirect prompt injection attempts
SUSPICIOUS_PATTERNS = [
    r"ignore\s+(all\s+)?(the\s+)?previous\s+instructions",
    r"ignore\s+les\s+instructions\s+pr[ée]c[ée]dentes",
    r"disregard\s+prior\s+rules",
    r"oublie\s+toutes\s+les\s+consignes",
    r"system\s*prompt\s*exfiltration",
    r"r[ée]v[èe]le\s+(le\s+)?prompt\s+syst[èe]me",
    r"envoie\s+(tous\s+)?les\s+rapports\s+vers",
    r"send\s+(all\s+)?data\s+to",
    r"curl\s+https?://",
    r"webhook",
    r"act\s+as\s+(an\s+)?unrestricted",
    r"mode\s+dan",
    r"bypass\s+security",
    r"élévation\s+de\s+privilèges",
    r"sudo\s+make\s+ticket",
]

COMPILED_PATTERNS = [re.compile(p, re.IGNORECASE) for p in SUSPICIOUS_PATTERNS]

class PromptInjectionGuard:
    @staticmethod
    def inspect_text(text: str) -> Tuple[bool, List[str]]:
        """Inspects arbitrary text (user input, OCR chunk, or tool response)
        for injection markers.
        
        Returns:
            (is_safe, reasons)
        """
        if not text:
            return True, []

        detected_violations = []
        for pattern in COMPILED_PATTERNS:
            match = pattern.search(text)
            if match:
                detected_violations.append(f"Pattern detected: '{match.group(0)}'")

        is_safe = len(detected_violations) == 0
        return is_safe, detected_violations

    @staticmethod
    def sanitize_untrusted_data(data_content: str) -> str:
        """Wraps untrusted external data (documents, OCR text) in strict XML boundary tags
        so LLM parsers treat them strictly as data and not instructions.
        """
        cleaned = data_content.replace("```", "'''")
        return f"<UNTRUSTED_DOCUMENT_DATA>\n{cleaned}\n</UNTRUSTED_DOCUMENT_DATA>"
