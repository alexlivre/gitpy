"""
Central module for git-scanner functionality.
"""
import os
import subprocess
from typing import Any, Dict

from .dlc import smart_pack_diff


def run_git_cmd(args: list, cwd: str) -> str:
    """Helper para executar comandos git de leitura."""
    result = subprocess.run(
        ["git"] + args,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='replace'
    )
    if result.returncode != 0:
        raise Exception(result.stderr.strip())
    return result.stdout.strip()


def process(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analisa o estado do repositório Git.
    """
    repo_path = payload.get("repo_path")
    max_diff = payload.get("max_diff_chars", 100000)  # 100KB default
    cid = payload.get("cid", "unknown")

    if not repo_path or not os.path.isdir(repo_path):
        return {"is_repo": False, "error": "NOT_DIR", "cid": cid}

    try:
        # 1. Verifica se é repo Git
        subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=repo_path,
            check=True,
            capture_output=True
        )
    except subprocess.CalledProcessError:
        return {"is_repo": False}

    try:
        # 2. Coleta Estado Básico
        branch = run_git_cmd(["branch", "--show-current"], repo_path)
        remotes = run_git_cmd(["remote"], repo_path)
        has_remote = bool(remotes)

        # 3. Verifica Mudanças
        # --porcelain garante formato estável para scripts
        status = run_git_cmd(["status", "--porcelain"], repo_path)
        has_changes = bool(status)

        files_changed = []
        if has_changes:
            # Lista simples de arquivos modificados
            files_changed = [line.strip().split()[-1]
                             for line in status.splitlines()]

        # 4. Captura Diff (Se houver mudanças e solicitado)
        diff_data = {"mode": "none"}
        if has_changes:
            # Intent-to-add: faz com que arquivos untracked (novos)
            # apareçam no diff sem realmente fazer stage completo
            try:
                subprocess.run(
                    ["git", "add", "-N", "."],
                    cwd=repo_path, capture_output=True
                )
            except:
                pass

            # Pega tanto staged quanto unstaged
            # diff HEAD mostra tudo que mudou desde o último commit
            try:
                full_diff = run_git_cmd(["diff", "HEAD"], repo_path)
            except:
                # Caso seja repo novo sem commits (HEAD inválido)
                try:
                    full_diff = run_git_cmd(["diff", "--cached"], repo_path)
                except:
                    full_diff = run_git_cmd(["diff"], repo_path)

            diff_data = smart_pack_diff(full_diff, max_chars=max_diff)

        return {
            "is_repo": True,
            "branch": branch,
            "has_remote": has_remote,
            "has_changes": has_changes,
            "files_changed": files_changed,
            "diff_data": diff_data
        }

    except Exception as e:
        return {
            "is_repo": True,
            "error": "SCAN_FAIL",
            "message": str(e),
            "cid": cid
        }
