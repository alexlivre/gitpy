import subprocess
from typing import Dict, Any

def analyze_history(repo_path: str, depth: int = 10) -> str:
    """
    Analisa os últimos N commits para extrair o estilo.
    """
    try:
        result = subprocess.run(
            ["git", "log", f"-n {depth}", "--pretty=format:%s"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        commits = result.stdout.splitlines()
    except:
        return ""

    if not commits:
        return ""

    # Heurísticas Simples
    has_conventional = any(c.startswith(("feat:", "fix:", "chore:", "docs:")) for c in commits)
    has_emoji = any(ord(c[0]) > 10000 for c in commits if c) # Check bobo de emoji no começo

    style_guide = "ESTILO DO PROJETO DETECTADO:\n"
    if has_conventional:
        style_guide += "- USE Conventional Commits (ex: 'feat: ...', 'fix: ...').\n"
    else:
        style_guide += "- USE estilo livre (Freeform).\n"
    
    if has_emoji:
        style_guide += "- USE Emojis no início (gitmoji padrão).\n"
    else:
        style_guide += "- NÃO use emojis.\n"
        
    style_guide += "- Mantenha a consistência com os commits anteriores.\n"
    
    return style_guide

def process(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Style Engine.
    """
    repo_path = payload.get("repo_path")
    
    if not repo_path:
        return {"error": "REPO_PATH_MISSING"}

    instructions = analyze_history(repo_path)
    
    return {
        "style_instructions": instructions or "Adote um estilo padrão profissional (Conventional Commits).",
        "detected": bool(instructions)
    }

