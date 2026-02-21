from typing import Dict, Any, List
from .dlc import check_is_blocked

def process(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Porteiro de Segurança (Sanitizer).
    Valida caminhos de arquivos contra a Blocklist Imutável.
    """
    files = payload.get("file_paths", [])
    action = payload.get("action", "validate")
    cid = payload.get("cid", "unknown")

    if not files:
        return {"safe_files": [], "blocked_files": [], "violations": 0}

    safe_files = []
    blocked_files = []
    violations = 0

    for f in files:
        if check_is_blocked(f):
            blocked_files.append(f)
            violations += 1
        else:
            safe_files.append(f)

    return {
        "action": action,
        "safe_files": safe_files,
        "blocked_files": blocked_files,
        "violations": violations
    }
