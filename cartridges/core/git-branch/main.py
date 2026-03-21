"""
Central module for git-branch functionality.
"""
import logging
import os
import re
import subprocess
from typing import Any, Dict

# Configuração de Logs
logger = logging.getLogger("git-branch")

# Padrão regex para validação de nomes de branches Git
# Baseado nas regras do Git: não pode começar com -, conter espaços, ou ter caracteres inválidos
BRANCH_NAME_PATTERN = re.compile(r'^[a-zA-Z0-9][a-zA-Z0-9._-]*$')


def run_git_cmd(args: list, cwd: str) -> str:
    """Helper para executar comandos git de leitura."""
    try:
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
    except FileNotFoundError:
        raise Exception("Executável 'git' não encontrado no PATH.")


def validate_branch_name(branch_name: str) -> Dict[str, Any]:
    """
    Valida se o nome da branch segue as regras do Git.
    
    Args:
        branch_name: Nome da branch a validar
        
    Returns:
        Dict com validação e mensagem de erro se aplicável
    """
    if not branch_name:
        return {
            "valid": False,
            "error": "Nome da branch não pode ser vazio."
        }
    
    if len(branch_name) > 255:
        return {
            "valid": False,
            "error": "Nome da branch muito longo (máximo 255 caracteres)."
        }
    
    # Nomes reservados pelo Git
    reserved_names = {"HEAD", "master", "main", "develop", "feature", "release", "hotfix"}
    if branch_name in reserved_names:
        return {
            "valid": False,
            "error": f"'{branch_name}' é um nome reservado pelo Git."
        }
    
    # Verifica se corresponde ao padrão
    if not BRANCH_NAME_PATTERN.match(branch_name):
        return {
            "valid": False,
            "error": "Nome da branch contém caracteres inválidos. Use apenas letras, números, pontos, hífens e underscores, e não comece com caracteres especiais."
        }
    
    return {"valid": True}


def process(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Processa operações relacionadas a branches Git.
    
    Args:
        payload: {
            "action": str,        # "create", "switch", "current", "exists", "validate"
            "branch_name": str,   # Nome da branch (opcional para algumas ações)
            "repo_path": str,     # Caminho do repositório
            "cid": str            # Correlation ID (opcional)
        }
    """
    action = payload.get("action")
    branch_name = payload.get("branch_name")
    repo_path = payload.get("repo_path")
    cid = payload.get("cid", "unknown")
    
    if not repo_path or not os.path.isdir(repo_path):
        return {"success": False, "error": "INVALID_PATH", "message": "Caminho do repositório inválido.", "cid": cid}
    
    if not action:
        return {"success": False, "error": "MISSING_ACTION", "message": "Ação não especificada.", "cid": cid}
    
    try:
        # Verifica se estamos em um repositório Git
        run_git_cmd(["rev-parse", "--is-inside-work-tree"], repo_path)
    except Exception as e:
        return {"success": False, "error": "NOT_GIT_REPO", "message": f"Não é um repositório Git: {str(e)}", "cid": cid}
    
    try:
        if action == "validate":
            if not branch_name:
                return {"success": False, "error": "MISSING_BRANCH_NAME", "message": "Nome da branch não fornecido para validação.", "cid": cid}
            
            validation = validate_branch_name(branch_name)
            return {
                "success": validation["valid"],
                "valid": validation["valid"],
                "error": validation.get("error")
            }
        
        elif action == "current":
            try:
                current = run_git_cmd(["branch", "--show-current"], repo_path)
                return {
                    "success": True,
                    "current_branch": current
                }
            except Exception as e:
                # Se não conseguir obter branch atual (repo novo sem commits)
                try:
                    # Tenta obter branch atual de outra forma
                    current = run_git_cmd(["rev-parse", "--abbrev-ref", "HEAD"], repo_path)
                    return {
                        "success": True,
                        "current_branch": current
                    }
                except Exception:
                    return {
                        "success": True,
                        "current_branch": "HEAD"  # Repo sem commits
                    }
        
        elif action == "exists":
            if not branch_name:
                return {"success": False, "error": "MISSING_BRANCH_NAME", "message": "Nome da branch não fornecido.", "cid": cid}
            
            try:
                # Lista todas as branches (locais e remotas)
                branches = run_git_cmd(["branch", "-a"], repo_path)
                # Remove prefixos e espaços
                branch_list = []
                for line in branches.splitlines():
                    line = line.strip()
                    if line.startswith("*"):
                        line = line[1:].strip()
                    # Remove remotes/ prefix
                    if "/" in line:
                        line = line.split("/")[-1]
                    branch_list.append(line)
                
                exists = branch_name in branch_list
                return {
                    "success": True,
                    "exists": exists,
                    "branches": branch_list
                }
            except Exception as e:
                return {"success": False, "error": "BRANCH_CHECK_FAIL", "message": f"Erro ao verificar branches: {str(e)}", "cid": cid}
        
        elif action == "create":
            if not branch_name:
                return {"success": False, "error": "MISSING_BRANCH_NAME", "message": "Nome da branch não fornecido.", "cid": cid}
            
            # Primeiro valida o nome
            validation = validate_branch_name(branch_name)
            if not validation["valid"]:
                return {
                    "success": False,
                    "error": "INVALID_BRANCH_NAME",
                    "message": f"Nome de branch inválido: {validation['error']}",
                    "cid": cid
                }
            
            try:
                # Verifica se já existe
                exists_check = process({
                    "action": "exists",
                    "branch_name": branch_name,
                    "repo_path": repo_path
                })
                
                if exists_check.get("exists"):
                    return {
                        "success": False,
                        "error": f"Branch '{branch_name}' já existe."
                    }
                
                # Cria a branch
                run_git_cmd(["branch", branch_name], repo_path)
                
                return {
                    "success": True,
                    "message": f"Branch '{branch_name}' criada com sucesso."
                }
            except Exception as e:
                return {"success": False, "error": "BRANCH_CREATE_FAIL", "message": f"Erro ao criar branch: {str(e)}", "cid": cid}
        
        elif action == "switch":
            if not branch_name:
                return {"success": False, "error": "MISSING_BRANCH_NAME", "message": "Nome da branch não fornecido.", "cid": cid}
            
            try:
                # Verifica se a branch existe
                exists_check = process({
                    "action": "exists", 
                    "branch_name": branch_name,
                    "repo_path": repo_path
                })
                
                if not exists_check.get("exists"):
                    return {
                        "success": False,
                        "error": f"Branch '{branch_name}' não existe."
                    }
                
                # Alterna para a branch
                run_git_cmd(["checkout", branch_name], repo_path)
                
                return {
                    "success": True,
                    "message": f"Alternado para branch '{branch_name}'."
                }
            except Exception as e:
                return {"success": False, "error": "BRANCH_SWITCH_FAIL", "message": f"Erro ao alternar branch: {str(e)}", "cid": cid}
        
        else:
            return {"success": False, "error": "UNSUPPORTED_ACTION", "message": f"Ação '{action}' não suportada.", "cid": cid}
    
    except Exception as e:
        logger.error(f"Erro em git-branch: {str(e)}")
        return {"success": False, "error": "UNEXPECTED_ERROR", "message": f"Erro inesperado: {str(e)}", "cid": cid}
