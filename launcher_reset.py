"""
Reset do GitPy - Restauração do repositório.
"""
import os
import subprocess
import sys

import typer
from rich.console import Console
from rich.panel import Panel

from i18n import t
from launcher_shared import _resolve_repo_path, app_dir
from launcher_menu import _inquirer_text, _inquirer_confirm, _collect_reset_options_from_menu


def _run_git_reset_resource(ctx: typer.Context) -> bool:
    """Retorna True se executou uma ação, False se usuário voltou."""
    console = Console()
    repo_path = _resolve_repo_path(ctx)
    options = _collect_reset_options_from_menu()

    if options is None:
        # Usuário escolheu voltar
        return False

    if options.mode == "full":
        danger_ack = _inquirer_text(
            t("menu_reset_confirm_phrase_prompt"),
            default="",
            qmark="⚠",
        ).strip()
        if danger_ack.lower() == "back":
            return False
        if danger_ack.upper() != "RESET":
            console.print(f"[yellow]{t('op_cancelled')}[/yellow]")
            return True

    reset_script = os.path.join(app_dir, "git_reset_to_github.py")
    command = [sys.executable, reset_script]
    if options.mode == "summary":
        command.append("--summary")
    elif options.mode == "dry_run":
        command.append("--dry-run")
    if options.quiet:
        command.append("--quiet")

    console.print(
        Panel(
            f"[bold cyan]{t('menu_reset_running')}[/bold cyan]\n"
            f"[white]{' '.join(command)}[/white]",
            border_style="cyan",
            title=t("menu_reset_title"),
        )
    )

    result = subprocess.run(command, cwd=repo_path, text=True, encoding="utf-8", errors="replace")
    if result.returncode == 0:
        console.print(f"[bold green]{t('menu_reset_done_success')}[/bold green]")
    else:
        console.print(f"[bold red]{t('menu_reset_done_fail')} (exit={result.returncode})[/bold red]")
    return True
