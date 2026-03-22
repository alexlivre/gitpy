"""Central module for git-tag functionality."""
import logging
import os
import random
import re
import string
import subprocess
from typing import Any, Dict, List

logger = logging.getLogger("git-tag")
TAG_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9._-]+$")


def run_git_cmd(args: list, cwd: str) -> str:
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if result.returncode != 0:
            raise Exception(result.stderr.strip())
        return result.stdout.strip()
    except FileNotFoundError:
        raise Exception("Executável 'git' não encontrado no PATH.")


def generate_confirmation_code() -> str:
    """Generate confirmation code in format LETTER-NUMBER-LETTER-LETTER."""
    letters = string.ascii_uppercase
    numbers = string.digits
    return (
        random.choice(letters)
        + random.choice(numbers)
        + random.choice(letters)
        + random.choice(letters)
    )


def validate_tag_name(tag_name: str) -> Dict[str, Any]:
    if not tag_name:
        return {"valid": False, "error": "Nome da tag não pode ser vazio."}
    if len(tag_name) > 255:
        return {"valid": False, "error": "Nome da tag muito longo (máximo 255 caracteres)."}
    if not TAG_NAME_PATTERN.match(tag_name):
        return {
            "valid": False,
            "error": "Nome da tag contém caracteres inválidos. Use letras, números, pontos, hífens e underscores.",
        }
    return {"valid": True}


def _list_local_tags(repo_path: str) -> List[str]:
    try:
        output = run_git_cmd(["tag", "--list"], repo_path)
        return [tag.strip() for tag in output.splitlines() if tag.strip()] if output else []
    except Exception:
        return []


def _list_remote_tags(repo_path: str) -> List[str]:
    try:
        output = run_git_cmd(["ls-remote", "--tags", "origin"], repo_path)
        tags = []
        for line in output.splitlines():
            if line.strip() and "\t" in line:
                tag_ref = line.split("\t")[1].strip()
                if tag_ref.startswith("refs/tags/"):
                    tag_name = tag_ref[10:]  # Remove "refs/tags/" prefix
                    if tag_name and not tag_name.endswith("^{}"):
                        tags.append(tag_name)
        return tags
    except Exception:
        return []


def _get_current_commit(repo_path: str) -> str:
    return run_git_cmd(["rev-parse", "HEAD"], repo_path)


def _is_working_tree_clean(repo_path: str) -> bool:
    try:
        run_git_cmd(["diff-index", "--quiet", "HEAD", "--"], repo_path)
        return True
    except Exception:
        return False


def process(payload: Dict[str, Any]) -> Dict[str, Any]:
    action = payload.get("action")
    tag_name = payload.get("tag_name")
    repo_path = payload.get("repo_path")
    cid = payload.get("cid", "unknown")

    if not repo_path or not os.path.isdir(repo_path):
        return {"success": False, "error": "INVALID_PATH", "message": "Caminho do repositório inválido.", "cid": cid}
    if not action:
        return {"success": False, "error": "MISSING_ACTION", "message": "Ação não especificada.", "cid": cid}

    try:
        run_git_cmd(["rev-parse", "--is-inside-work-tree"], repo_path)
    except Exception as exc:
        return {"success": False, "error": "NOT_GIT_REPO", "message": f"Não é um repositório Git: {exc}", "cid": cid}

    try:
        if action == "validate":
            if not tag_name:
                return {"success": False, "error": "MISSING_TAG_NAME", "message": "Nome da tag não fornecido.", "cid": cid}
            validation = validate_tag_name(tag_name)
            return {"success": validation["valid"], "valid": validation["valid"], "error": validation.get("error"), "cid": cid}

        if action == "list":
            local_tags = _list_local_tags(repo_path)
            remote_tags = _list_remote_tags(repo_path)
            return {
                "success": True,
                "local_tags": local_tags,
                "remote_tags": remote_tags,
                "cid": cid,
            }

        if action == "exists":
            if not tag_name:
                return {"success": False, "error": "MISSING_TAG_NAME", "message": "Nome da tag não fornecido.", "cid": cid}
            local_tags = _list_local_tags(repo_path)
            exists = tag_name in local_tags
            return {"success": True, "exists": exists, "tags": local_tags, "cid": cid}

        if action == "create":
            if not tag_name:
                return {"success": False, "error": "MISSING_TAG_NAME", "message": "Nome da tag não fornecido.", "cid": cid}
            validation = validate_tag_name(tag_name)
            if not validation["valid"]:
                return {"success": False, "error": "INVALID_TAG_NAME", "message": f"Nome de tag inválido: {validation['error']}", "cid": cid}
            if process({"action": "exists", "tag_name": tag_name, "repo_path": repo_path}).get("exists"):
                return {"success": False, "error": "TAG_EXISTS", "message": f"Tag '{tag_name}' já existe.", "cid": cid}
            
            message = payload.get("message")
            if message:
                run_git_cmd(["tag", "-a", tag_name, "-m", message], repo_path)
            else:
                run_git_cmd(["tag", tag_name], repo_path)
            
            # Try to push tag to remote (with warning if fails)
            remote_push_failed = False
            try:
                run_git_cmd(["push", "origin", tag_name], repo_path)
            except Exception:
                remote_push_failed = True
            
            message = f"Tag '{tag_name}' criada com sucesso."
            if remote_push_failed:
                message += " Aviso: Falha ao enviar tag para o repositório remoto."
            else:
                message += " Tag enviada para o repositório remoto."
            
            return {"success": True, "message": message, "cid": cid}

        if action == "delete":
            if not tag_name:
                return {"success": False, "error": "MISSING_TAG_NAME", "message": "Nome da tag não fornecido.", "cid": cid}
            
            # Check if confirmation code is provided
            confirmation_code = payload.get("confirmation_code")
            if not confirmation_code:
                code = generate_confirmation_code()
                return {
                    "success": False,
                    "error": "CONFIRMATION_REQUIRED",
                    "message": f"Para deletar a tag '{tag_name}', digite o código: {code}",
                    "confirmation_code": code,
                    "cid": cid,
                }
            
            # Validate confirmation code
            expected_code = payload.get("expected_code")
            if confirmation_code.upper() != expected_code.upper():
                return {"success": False, "error": "INVALID_CONFIRMATION", "message": "Código de confirmação inválido.", "cid": cid}
            
            # Check if tag exists
            if not process({"action": "exists", "tag_name": tag_name, "repo_path": repo_path}).get("exists"):
                return {"success": False, "error": "TAG_NOT_FOUND", "message": f"Tag '{tag_name}' não encontrada.", "cid": cid}
            
            # Delete local tag
            try:
                run_git_cmd(["tag", "-d", tag_name], repo_path)
            except Exception as exc:
                return {"success": False, "error": "UNEXPECTED_ERROR", "message": f"Falha ao deletar tag local: {exc}", "cid": cid}
            
            # Try to delete remote tag (with warning if fails)
            remote_delete_failed = False
            try:
                run_git_cmd(["push", "origin", "--delete", tag_name], repo_path)
            except Exception:
                remote_delete_failed = True
            
            message = f"Tag '{tag_name}' deletada com sucesso."
            if remote_delete_failed:
                message += " Aviso: Falha ao deletar tag no repositório remoto."
            
            return {"success": True, "message": message, "cid": cid}

        if action == "reset":
            if not tag_name:
                return {"success": False, "error": "MISSING_TAG_NAME", "message": "Nome da tag não fornecido.", "cid": cid}
            
            # Check if confirmation code is provided
            confirmation_code = payload.get("confirmation_code")
            if not confirmation_code:
                code = generate_confirmation_code()
                return {
                    "success": False,
                    "error": "CONFIRMATION_REQUIRED",
                    "message": f"Para resetar para a tag '{tag_name}', digite o código: {code}",
                    "confirmation_code": code,
                    "cid": cid,
                }
            
            # Validate confirmation code
            expected_code = payload.get("expected_code")
            if confirmation_code.upper() != expected_code.upper():
                return {"success": False, "error": "INVALID_CONFIRMATION", "message": "Código de confirmação inválido.", "cid": cid}
            
            # Check if tag exists
            if not process({"action": "exists", "tag_name": tag_name, "repo_path": repo_path}).get("exists"):
                return {"success": False, "error": "TAG_NOT_FOUND", "message": f"Tag '{tag_name}' não encontrada.", "cid": cid}
            
            # Check if working tree is clean
            if not _is_working_tree_clean(repo_path):
                return {"success": False, "error": "RESET_DIRTY_WORKTREE", "message": "Working tree sujo. Faça commit ou stash antes de resetar.", "cid": cid}
            
            # Reset to tag
            run_git_cmd(["reset", "--hard", tag_name], repo_path)
            return {"success": True, "message": f"Repositório resetado para a tag '{tag_name}'.", "cid": cid}

        return {"success": False, "error": "UNSUPPORTED_ACTION", "message": f"Ação '{action}' não suportada.", "cid": cid}
    except Exception as exc:
        logger.error("Erro em git-tag: %s", exc)
        return {"success": False, "error": "UNEXPECTED_ERROR", "message": f"Erro inesperado: {exc}", "cid": cid}
