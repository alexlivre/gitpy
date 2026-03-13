"""
Central module for sec-redactor functionality.
"""
import re
from typing import Any, Dict

# Padrões de Redação (Data Masking)
PATTERNS = {
    "Email": r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+",
    "URL_Auth": r"(https?://)[^@]+@([a-zA-Z0-9.-]+)",  # http://user:pass@host
    "AWS_Key": r"(AKIA|ASIA)[0-9A-Z]{16}",
    "Private_Key": r"-----BEGIN [A-Z ]+ PRIVATE KEY-----",
    "Google_API": r"AIza[0-9A-Za-z-_]{35}",
    # Token genérico
    "Generic_Token": r"(bearer|token|key)[=: ]+[A-Za-z0-9_\-\.]{20,}",
    "IP_Address": r"\b(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b"
}

COMPILED_PATTERNS = {name: re.compile(
    regex, re.IGNORECASE) for name, regex in PATTERNS.items()}


def redact_text(text: str) -> dict:
    redacted_text = text
    matches = []
    count = 0

    for name, pattern in COMPILED_PATTERNS.items():
        # Encontra todas as ocorrências
        found = pattern.findall(redacted_text)
        if found:
            # Log parcial seguro
            matches.extend([f"{name}: {m[:4]}..." for m in found])
            count += len(found)
            # Substitui por placeholder
            redacted_text = pattern.sub(f"[REDACTED:{name}]", redacted_text)

    return {
        "text": redacted_text,
        "count": count,
        "types": list(set([m.split(":")[0] for m in matches]))
    }


def process(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitiza conteúdo textual (Data Masking).
    Input: content (str)
    """
    content = payload.get("content")
    cid = payload.get("cid", "unknown")

    if not content:
        return {"sanitized_content": "", "redacted_count": 0}

    result = redact_text(content)

    return {
        "sanitized_content": result["text"],
        "redacted_count": result["count"],
        "patterns_found": result["types"]
    }
