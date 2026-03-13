"""
Central module for cli-renderer functionality.
"""
from typing import Any, Dict

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

console = Console()


def render_diff(diff_text: str):
    """Renderiza diff com syntax highlighting."""
    if not diff_text:
        return
    syntax = Syntax(diff_text, "diff", theme="monokai", line_numbers=False)
    console.print(Panel(syntax, title="🔍 Review Changes", border_style="blue"))


def render_success(msg: str):
    console.print(Panel(msg, title="✨ Success", border_style="green"))


def render_error(msg: str):
    console.print(Panel(msg, title="❌ Error", border_style="red"))


def process(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Renderizador Visual (CLI).
    Action: status_panel | diff_panel | error | success
    """
    action = payload.get("action")
    data = payload.get("data", {})
    msg = payload.get("message", "")

    if action == "diff_panel":
        diff = data.get("diff", "")
        render_diff(diff)
        return {"rendered": True}

    elif action == "success":
        render_success(msg)
        return {"rendered": True}

    elif action == "error":
        render_error(msg)
        return {"rendered": True}

    elif action == "spinner":
        # Nota: Spinners em arquitetura "stateless" de cartucho são complexos.
        # O ideal é o launcher.py controlar o contexto `with Progress...`
        # Aqui apenas forneceríamos os componentes.
        return {"rendered": False, "note": "Spinners should be handled by the context manager in launcher.py"}

    return {"rendered": False, "error": "UNKNOWN_ACTION"}
