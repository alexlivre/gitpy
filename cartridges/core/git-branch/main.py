"""Central module for git-branch functionality."""
import logging
import os
import re
import subprocess
from typing import Any, Dict, List

logger = logging.getLogger("git-branch")
BRANCH_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._-]*$")


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


def validate_branch_name(branch_name: str) -> Dict[str, Any]:
    if not branch_name:
        return {"valid": False, "error": "Nome da branch não pode ser vazio."}
    if len(branch_name) > 255:
        return {"valid": False, "error": "Nome da branch muito longo (máximo 255 caracteres)."}
    if branch_name in {"HEAD", "master", "main", "develop", "feature", "release", "hotfix"}:
        return {"valid": False, "error": f"'{branch_name}' é um nome reservado pelo Git."}
    if not BRANCH_NAME_PATTERN.match(branch_name):
        return {
            "valid": False,
            "error": "Nome da branch contém caracteres inválidos. Use letras, números, pontos, hífens e underscores.",
        }
    return {"valid": True}


def _get_current_branch(repo_path: str) -> str:
    current = run_git_cmd(["branch", "--show-current"], repo_path)
    if current:
        return current
    current = run_git_cmd(["rev-parse", "--abbrev-ref", "HEAD"], repo_path)
    return current or "HEAD"


def _list_branches(repo_path: str) -> Dict[str, Any]:
    raw = run_git_cmd(["branch", "-a"], repo_path)
    current = _get_current_branch(repo_path)
    local_branches: List[str] = []
    remote_branches: List[str] = []
    all_branch_names = set()

    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("*"):
            line = line[1:].strip()
        if line.startswith("remotes/"):
            remote_ref = line[len("remotes/"):]
            if " -> " in remote_ref:
                continue
            remote_branches.append(remote_ref)
            name = remote_ref.split("/", 1)[1] if "/" in remote_ref else remote_ref
            if name:
                all_branch_names.add(name)
            continue
        local_branches.append(line)
        all_branch_names.add(line)

    return {
        "success": True,
        "current_branch": current,
        "local_branches": local_branches,
        "remote_branches": remote_branches,
        "all_branch_names": sorted(all_branch_names),
    }


def process(payload: Dict[str, Any]) -> Dict[str, Any]:
    action = payload.get("action")
    branch_name = payload.get("branch_name")
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
            if not branch_name:
                return {"success": False, "error": "MISSING_BRANCH_NAME", "message": "Nome da branch não fornecido.", "cid": cid}
            validation = validate_branch_name(branch_name)
            return {"success": validation["valid"], "valid": validation["valid"], "error": validation.get("error"), "cid": cid}

        if action == "current":
            return {"success": True, "current_branch": _get_current_branch(repo_path), "cid": cid}

        if action == "list":
            result = _list_branches(repo_path)
            result["cid"] = cid
            return result

        if action == "exists":
            if not branch_name:
                return {"success": False, "error": "MISSING_BRANCH_NAME", "message": "Nome da branch não fornecido.", "cid": cid}
            listed = _list_branches(repo_path)
            exists = branch_name in listed.get("all_branch_names", [])
            return {"success": True, "exists": exists, "branches": listed.get("all_branch_names", []), "cid": cid}

        if action == "create":
            if not branch_name:
                return {"success": False, "error": "MISSING_BRANCH_NAME", "message": "Nome da branch não fornecido.", "cid": cid}
            validation = validate_branch_name(branch_name)
            if not validation["valid"]:
                return {"success": False, "error": "INVALID_BRANCH_NAME", "message": f"Nome de branch inválido: {validation['error']}", "cid": cid}
            if process({"action": "exists", "branch_name": branch_name, "repo_path": repo_path}).get("exists"):
                return {"success": False, "error": f"Branch '{branch_name}' já existe.", "cid": cid}
            run_git_cmd(["branch", branch_name], repo_path)
            return {"success": True, "message": f"Branch '{branch_name}' criada com sucesso.", "cid": cid}

        if action == "switch":
            if not branch_name:
                return {"success": False, "error": "MISSING_BRANCH_NAME", "message": "Nome da branch não fornecido.", "cid": cid}
            if not process({"action": "exists", "branch_name": branch_name, "repo_path": repo_path}).get("exists"):
                return {"success": False, "error": f"Branch '{branch_name}' não existe.", "cid": cid}
            run_git_cmd(["checkout", branch_name], repo_path)
            return {"success": True, "message": f"Alternado para branch '{branch_name}'.", "cid": cid}

        if action == "delete":
            if not branch_name:
                return {"success": False, "error": "MISSING_BRANCH_NAME", "message": "Nome da branch não fornecido.", "cid": cid}
            if branch_name == _get_current_branch(repo_path):
                return {"success": False, "error": "CANNOT_DELETE_CURRENT", "message": "Não é possível deletar a branch atual.", "cid": cid}
            force = bool(payload.get("force", False))
            run_git_cmd(["branch", "-D" if force else "-d", branch_name], repo_path)
            return {"success": True, "message": f"Branch '{branch_name}' deletada com sucesso.", "cid": cid}

        if action == "push_branch":
            if not branch_name:
                return {"success": False, "error": "MISSING_BRANCH_NAME", "message": "Nome da branch não fornecido.", "cid": cid}
            remote = payload.get("remote", "origin")
            run_git_cmd(["push", "-u", remote, branch_name], repo_path)
            return {"success": True, "message": f"Branch '{branch_name}' enviada para '{remote}'.", "cid": cid}

        return {"success": False, "error": "UNSUPPORTED_ACTION", "message": f"Ação '{action}' não suportada.", "cid": cid}
    except Exception as exc:
        logger.error("Erro em git-branch: %s", exc)
        return {"success": False, "error": "UNEXPECTED_ERROR", "message": f"Erro inesperado: {exc}", "cid": cid}
