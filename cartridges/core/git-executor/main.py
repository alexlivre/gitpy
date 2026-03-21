"""
Central module for git-executor functionality.
"""
import logging
import os
import shlex
import subprocess
from typing import Any, Dict

# Configuração de Logs
logger = logging.getLogger("git-executor")

# WHITELIST: Comandos permitidos para execução direta
# Qualquer comando fora desta lista será rejeitado por segurança.
ALLOWED_COMMANDS = {
    "init", "status", "diff", "add", "commit",
    "push", "pull", "fetch", "branch", "checkout",
    "merge", "rebase", "log", "remote", "config",
    "rev-parse", "ls-files", "reset", "rm"
}

# BLACKLIST: Argumentos perigosos que devem ser bloqueados
BLOCKED_ARGS = [
    "--hard",             # Reset hard (perigo de perda de dados sem backup)
    # Push force (perigo de reescrever histórico compartilhado)
    "--force", "-f",
    "clean"               # Git clean (remove arquivos untracked)
]


def validate_command(command_str: str) -> bool:
    """
    Valida se o comando é seguro para execução.
    Regra 1: Deve começar com um subcomando permitido.
    Regra 2: Não pode conter argumentos da blacklist.
    """
    parts = shlex.split(command_str)
    if not parts:
        return False

    subcommand = parts[0]

    # Validação de Subcomando
    if subcommand not in ALLOWED_COMMANDS:
        logger.warning(f"Comando bloqueado (não permitido): git {subcommand}")
        return False

    # Regra Especial: 'rm' só é permitido com '--cached' (para evitar deleção de arquivos)
    if subcommand == "rm" and "--cached" not in parts:
        logger.warning(
            "Comando bloqueado: 'git rm' requer '--cached' para segurança.")
        return False

    # Validação de Argumentos Perigosos
    for arg in parts:
        if arg in BLOCKED_ARGS:
            # Exceção: --force-with-lease é permitido
            if arg == "--force" and "--force-with-lease" in parts:
                continue
            logger.warning(f"Comando bloqueado (argumento perigoso): {arg}")
            return False

    return True


def process(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Executa um comando Git de forma segura.

    Args:
        payload: {
            "repo_path": str,  # Caminho raiz do repositório
            "command": str,    # Comando git (sem o prefixo 'git ')
            "dry_run": bool    # Se True, apenas simula
        }
    """
    repo_path = payload.get("repo_path")
    command = payload.get("command")
    dry_run = payload.get("dry_run", False)
    cid = payload.get("cid", "unknown")

    if not repo_path or not command:
        return {"success": False, "error": "MISSING_ARGS", "message": "Parâmetros 'repo_path' e 'command' são obrigatórios.", "cid": cid}

    # 1. Validação de Segurança (Whitelist)
    if not validate_command(command):
        return {
            "success": False,
            "error": "CMD_BLOCKED",
            "message": f"O comando 'git {command}' foi bloqueado pela política de segurança.",
            "cid": cid
        }

    full_cmd = f"git {command}"

    # 2. Dry Run (Simulação)
    if dry_run:
        return {
            "success": True,
            "stdout": f"[DRY-RUN] Executaria: {full_cmd}",
            "stderr": "",
            "return_code": 0
        }

    try:
        # 3. Execução Real via Subprocess
        # shell=False e shlex.split para evitar Command Injection
        args = ["git"] + shlex.split(command)

        # Prepara ambiente não-interativo
        env = os.environ.copy()
        env["GIT_TERMINAL_PROMPT"] = "0"
        env["GIT_EDITOR"] = "true"  # Evita abrir editor em rebase/merge

        result = subprocess.run(
            args,
            cwd=repo_path,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',  # Evita crash com caracteres estranhos
            env=env
        )

        return {
            "success": result.returncode == 0,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
            "return_code": result.returncode
        }

    except FileNotFoundError:
        return {"success": False, "error": "GIT_NOT_FOUND", "message": "Executável 'git' não encontrado no PATH.", "cid": cid}
    except Exception as e:
        return {"success": False, "error": "EXEC_FAIL", "message": str(e), "cid": cid}
