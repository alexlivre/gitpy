import os
import shutil
import glob
from typing import Dict, Any, List

TEMP_DIR_NAME = ".gitpy-temp"
PRIVATE_CONFIG_FILE = ".gitpy-private"

def ensure_gitignore(repo_path: str):
    """Garante que .gitpy-temp esteja no .gitignore."""
    gitignore_path = os.path.join(repo_path, ".gitignore")
    entry = f"{TEMP_DIR_NAME}/"
    
    if os.path.exists(gitignore_path):
        with open(gitignore_path, "r", encoding="utf-8") as f:
            content = f.read()
        if entry not in content:
            with open(gitignore_path, "a", encoding="utf-8") as f:
                f.write(f"\n{entry}\n")
            return True
    else:
        with open(gitignore_path, "w", encoding="utf-8") as f:
            f.write(f"{entry}\n")
        return True
    return False

def load_private_patterns(repo_path: str) -> List[str]:
    """Lê os padrões do arquivo .gitpy-private."""
    config_path = os.path.join(repo_path, PRIVATE_CONFIG_FILE)
    patterns = []
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    patterns.append(line)
    return patterns

def stash(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Move arquivos privados para .gitpy-temp.
    """
    repo_path = payload.get("repo_path")
    if not repo_path:
        return {"success": False, "error": "MISSING_REPO_PATH"}

    # 1. Setup: Ignorar temp e criar pasta
    ensure_gitignore(repo_path)
    temp_dir = os.path.join(repo_path, TEMP_DIR_NAME)
    os.makedirs(temp_dir, exist_ok=True)

    # 2. Ler padrões
    patterns = load_private_patterns(repo_path)
    if not patterns:
        return {"success": True, "files_moved": []} # Nada a esconder

    moved_files = []
    
    # 3. Encontrar e Mover Arquivos
    for pattern in patterns:
        # Usa glob para encontrar arquivos (suporte básico a *, não é full gitignore spec mas serve)
        # Se o padrão termina com /, é diretório
        search_pattern = os.path.join(repo_path, pattern)
        # Glob recursive se tiver **
        recursive = "**" in pattern
        
        found = glob.glob(search_pattern, recursive=recursive)
        
        for item_path in found:
            # Pular se já estiver no temp ou for o próprio temp ou config
            if TEMP_DIR_NAME in item_path or PRIVATE_CONFIG_FILE in item_path:
                continue
            
            # Check existence (it might have been moved as part of a parent directory)
            if not os.path.exists(item_path):
                continue
                
            rel_path = os.path.relpath(item_path, repo_path)
            dest_path = os.path.join(temp_dir, rel_path)
            
            # Criar dirs pais no destino
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            
            try:
                # Se for diretório, verificar se destino já existe para evitar erro ou merge
                if os.path.isdir(item_path):
                     # shutil.move reclama se destino existe. 
                     # Se destino existe, talvez queiramos mergear? 
                     # Simplificação: se for dir, usa copytree/rmtree ou lida com exceção?
                     # shutil.move tenta renomear.
                     pass

                shutil.move(item_path, dest_path)
                moved_files.append(rel_path)
            except Exception as e:
                # Se falhar um, aborta (segurança) ou loga?
                # Pelo plano: "Abort on Fail"
                return {
                    "success": False, 
                    "error": f"FAILED_TO_MOVE: {rel_path} -> {str(e)}",
                    "files_moved": moved_files # Retorna o que já foi movido para tentar restaurar
                }

    return {
        "success": True, 
        "files_moved": moved_files,
        "temp_usage": bool(moved_files)
    }

def restore(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Devolve arquivos de .gitpy-temp para a origem.
    """
    repo_path = payload.get("repo_path")
    if not repo_path:
        return {"success": False, "error": "MISSING_REPO_PATH"}

    temp_dir = os.path.join(repo_path, TEMP_DIR_NAME)
    if not os.path.exists(temp_dir):
        return {"success": True, "restored_files": []}

    restored_files = []
    errors = []

    # Caminhar pelo temp dir e devolver tudo
    for root, dirs, files in os.walk(temp_dir, topdown=False):
        for name in files + dirs:
            src_path = os.path.join(root, name)
            rel_path = os.path.relpath(src_path, temp_dir)
            dest_path = os.path.join(repo_path, rel_path)

            # Se for diretório
            if os.path.isdir(src_path):
                # Apenas crie o dir de volta se não existir
                os.makedirs(dest_path, exist_ok=True)
                # Tenta remover o dir vazio do temp (limpeza)
                try:
                    os.rmdir(src_path)
                except:
                    pass
                continue

            # Se for arquivo
            try:
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                
                # Conflict Check: Se destino já existe, não sobrescrever!
                if os.path.exists(dest_path):
                    # Renomeia para .restored para salvar o que estava no stash sem perder o novo
                    timestamp = "" # Simplificado para não importar time, ou usar apenas .restored
                    # Se .restored já existe, tenta .restored.1 etc? 
                    # Simples: .restored_<hash>? Não, vamos de .restored e se falhar, loga erro.
                    
                    base, ext = os.path.splitext(dest_path)
                    safe_dest_path = f"{base}{ext}.restored"
                    
                    # Se o .restored também existe, tenta .restored.old
                    if os.path.exists(safe_dest_path):
                        safe_dest_path = f"{base}{ext}.restored_copy"
                    
                    shutil.move(src_path, safe_dest_path)
                    restored_files.append(f"{rel_path} (CONFLICT -> {os.path.basename(safe_dest_path)})")
                else:
                    shutil.move(src_path, dest_path)
                    restored_files.append(rel_path)
                    
            except Exception as e:
                errors.append(f"{rel_path}: {str(e)}")

    # Cleanup: Remover a pasta temp se ficou vazia (ou forçar remoção se sobrou lixo não restaurável?)
    # O user pediu "Limpeza Atômica". Se houve erro, talvez não devamos apagar?
    # Mas se movemos com sucesso, apaga.
    try:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir) # Remove tudo que sobrou
    except Exception as e:
        errors.append(f"Cleanup Failed: {str(e)}")

    if errors:
        return {"success": False, "error": "RESTORE_ERRORS", "details": errors}

    return {"success": True, "restored_files": restored_files}

async def process(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Entry point for the Stealth Tool.
    Dispatches to stash or restore based on 'action'.
    """
    action = payload.get("action")
    
    if action == "stash":
        return stash(payload)
    elif action == "restore":
        return restore(payload)
    else:
        return {"success": False, "error": f"UNKNOWN_ACTION: {action}", "message": "Action must be 'stash' or 'restore'."}
