"""
Central module for tool-ignore functionality.
"""
import json
import os
from typing import Any, Dict, List


def load_common_trash() -> List[str]:
    """Carrega a lista de padrões comuns de 'lixo' do arquivo JSON ou usa lista padrão."""
    try:
        json_path = os.path.join(
            os.path.dirname(__file__), "common_trash.json")
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, Exception):
        # Lista padrão de segurança se o arquivo não existir ou estiver inválido
        return [".env", "node_modules/", "build/"]


# Carrega a lista de padrões comuns de "lixo" para sugerir
COMMON_TRASH = load_common_trash()


def get_ignore_path(base_path: str) -> str:
    return os.path.join(base_path, ".gitignore")


def read_ignore_file(path: str) -> List[str]:
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f.readlines() if line.strip() and not line.startswith("#")]


def parse_exceptions_from_gitignore(path: str) -> List[str]:
    """Parser de exceções do .gitignore - procura por comentário # ["item1", "item2"] do not ignore"""
    exceptions = []
    if not os.path.exists(path):
        return exceptions

    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("# [") and "do not ignore" in line:
                    # Extrai itens entre colchetes
                    start = line.find("[") + 1
                    end = line.find("]")
                    if start > 0 and end > start:
                        items_str = line[start:end]
                        # Parseia os itens, removendo aspas e espaços
                        items = [item.strip().strip('"').strip("'")
                                 for item in items_str.split(",")]
                        exceptions.extend(items)
    except Exception:
        pass  # Silenciosamente ignora erros de leitura

    return exceptions


def append_ignore_rule(path: str, pattern: str) -> bool:
    current_rules = read_ignore_file(path)
    if pattern in current_rules:
        return False

    with open(path, "a", encoding="utf-8") as f:
        # Garante nova linha se necessário
        f.write(f"\n{pattern}")
    return True


def check_env_security_exceptions(exceptions: List[str]) -> Dict[str, Any]:
    """Verifica se .env está na lista de exceções e retorna alerta de segurança"""
    if ".env" in exceptions:
        return {
            "alert": True,
            "message": "⚠️ ALERTA DE SEGURANÇA: O arquivo .env foi marcado para NÃO ser ignorado. Isso pode expor suas senhas no GitHub!",
            "requires_confirmation": True
        }
    return {"alert": False}


def scan_trash(base_path: str, existing_rules: List[str], ignore_path: str) -> Dict[str, Any]:
    """Escanear por trash com suporte a exceções e segurança .env"""
    suggestions = []

    # Parser exceções do .gitignore
    exceptions = parse_exceptions_from_gitignore(ignore_path)

    # Verifica segurança .env
    security_check = check_env_security_exceptions(exceptions)
    if security_check["alert"]:
        return {
            "success": False,
            "error": "SECURITY_ALERT",
            "message": security_check["message"],
            "requires_confirmation": True
        }

    candidates = set(COMMON_TRASH)

    # Remove exceções da lista de candidatos
    candidates = candidates - set(exceptions)

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

    return {"success": True, "suggestions": suggestions}


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
            result = scan_trash(base_path, rules, ignore_path)

            # Se houver alerta de segurança, retorna imediatamente
            if not result.get("success", False) and result.get("error") == "SECURITY_ALERT":
                return result

            # Caso contrário, retorna as sugestões normalmente
            return {"success": True, "suggestions": result.get("suggestions", [])}

        else:
            return {"success": False, "error": "INVALID_ACTION"}

    except Exception as e:
        return {"success": False, "error": "IGNORE_FAIL", "message": str(e)}
