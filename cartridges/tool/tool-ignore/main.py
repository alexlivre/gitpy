import os
from typing import Dict, Any, List

# Lista de padrões comuns de "lixo" para sugerir
COMMON_TRASH = [
    ".env",
    "__pycache__/",
    "*.pyc",
    "*.log",
    ".DS_Store",
    "node_modules/",
    "dist/",
    "build/",
    ".vscode/",
    ".idea/",
    "coverage/",
    "*.swp",
    ".gitpy-private"
]

def get_ignore_path(base_path: str) -> str:
    return os.path.join(base_path, ".gitignore")

def read_ignore_file(path: str) -> List[str]:
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f.readlines() if line.strip() and not line.startswith("#")]

def append_ignore_rule(path: str, pattern: str) -> bool:
    current_rules = read_ignore_file(path)
    if pattern in current_rules:
        return False
    
    with open(path, "a", encoding="utf-8") as f:
        # Garante nova linha se necessário
        f.write(f"\n{pattern}")
    return True

def scan_trash(base_path: str, existing_rules: List[str]) -> List[str]:
    suggestions = []

    candidates = set(COMMON_TRASH)

    for pattern in candidates:
        if pattern in existing_rules:
            continue

        # Simples heurística: se o arquivo/dir existe e não está no gitignore, sugere
        clean_pattern = pattern.rstrip("/")
        full_path = os.path.join(base_path, clean_pattern)

        if "*" in pattern:
             # Sempre sugere wildcards comuns se não estivem lá
             suggestions.append(pattern)
             continue

        if os.path.exists(full_path):
            suggestions.append(pattern)

    return suggestions

def process(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Gerenciador de .gitignore.
    Ações: 'add', 'list', 'scan'
    """
    action = payload.get("action", "list")
    base_path = payload.get("repo_path", ".")
    pattern = payload.get("pattern")
    
    ignore_path = get_ignore_path(base_path)
    
    try:
        if action == "add":
            if not pattern:
                return {"success": False, "error": "MISSING_PATTERN"}
            
            added = append_ignore_rule(ignore_path, pattern)
            if added:
                 return {"success": True, "message": f"Padrão '{pattern}' adicionado."}
            else:
                 return {"success": True, "message": f"Padrão '{pattern}' já existe."}

        elif action == "list":
            rules = read_ignore_file(ignore_path)
            return {"success": True, "rules": rules}

        elif action == "scan":
            rules = read_ignore_file(ignore_path)
            suggestions = scan_trash(base_path, rules)
            return {"success": True, "suggestions": suggestions}
            
        else:
             return {"success": False, "error": "INVALID_ACTION"}

    except Exception as e:
        return {"success": False, "error": "IGNORE_FAIL", "message": str(e)}
