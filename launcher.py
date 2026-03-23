"""
Central module for GitPy Launcher functionality.
"""
import os
import sys
from typing import Optional

import typer

# Fix Windows encoding: force UTF-8 to prevent 'charmap' codec errors with emojis
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from dotenv import load_dotenv

# Carrega configuracoes do servidor/ambiente IMEDIATAMENTE (essencial para i18n)
app_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(app_dir, ".env"))

from rich import box
from rich.console import Console
from rich.panel import Panel

import vibe_core
vibe_core.MENU_MODE = True

from vibe_core import kernel
from i18n import t
from navigation_stack import get_nav_stack

# Imports do módulo compartilhado (evita importação circular)
from launcher_shared import (
    AutoOptions,
    ResetOptions,
    run_async,
    _resolve_repo_path,
)

# Imports dos módulos auxiliares (refatoração VIBE_COMPLIANCE)
from launcher_menu import (
    MenuDependencyError,
    _load_inquirer,
    _inquirer_select,
    _inquirer_text,
    _inquirer_confirm,
    _menu_confirm,
    _inquirer_style,
    _render_menu_header,
    _pause_menu,
    _collect_auto_options_from_menu,
    _collect_reset_options_from_menu,
    _run_menu_mode,
    _get_menu_repo_status,
)
from launcher_branch import _run_branch_center
from launcher_diagnostics import _run_check_ai_diagnostics, _show_gitpy_resources
from launcher_reset import _run_git_reset_resource
from launcher_auto import _run_auto_with_guards, _run_auto_with_branch_guards


# Inicializa a aplicacao Typer
app = typer.Typer(
    help=t("app_help"),
    add_completion=False,
    no_args_is_help=False,
)


def _is_interactive_terminal() -> bool:
    """Detecta se a sessao atual suporta prompts interativos."""
    try:
        return sys.stdin.isatty() and sys.stdout.isatty()
    except Exception:
        return False


def _show_welcome_screen() -> None:
    console = Console()
    console.print(
        Panel.fit(
            "[bold purple]GitPy[/bold purple] [white]v1.0[/white]\n"
            f"[italic]{t('welcome_subtitle')}[/italic]",
            border_style="purple",
            box=box.ROUNDED,
        )
    )

    console.print(f"\n[bold]{t('usage_auto')}[/bold]")
    console.print(f"\n[bold]{t('useful_flags')}[/bold]")
    console.print(
        f"  [green]--debug[/green]      [bold magenta]Deep Trace Mode:[/bold magenta] {t('option_debug_help')}"
    )
    console.print(f"  [green]--dry-run[/green]    {t('flag_dry_run')}")
    console.print(f"  [green]--no-push[/green]    {t('flag_no_push')}")
    console.print(f"  [green]-m 'texto'[/green]   {t('flag_message')}")
    console.print(f"  [green]-y[/green]           {t('flag_yes')}")
    console.print(f"  [green]--model X[/green]    {t('flag_model')}")
    console.print(f"\n[dim]{t('help_hint')}[/dim]")


# ============================================================================
# FUNÇÕES MOVIDAS PARA MÓDULOS AUXILIARES (launcher_menu.py, etc.)
# As funções abaixo foram refatoradas para seguir VIBE_ENGINEERING_GUIDE.
# Imports no topo do arquivo trazem as implementações dos módulos.
# ============================================================================


# As seguintes funções foram movidas para os módulos auxiliares:
# - run_async, _resolve_repo_path, AutoOptions, ResetOptions -> launcher_shared.py
# - _get_menu_repo_status -> launcher_menu.py
# - _render_menu_header -> launcher_menu.py
# - _pause_menu -> launcher_menu.py
# - _run_check_ai_diagnostics -> launcher_diagnostics.py
# - _collect_auto_options_from_menu -> launcher_menu.py
# - _collect_reset_options_from_menu -> launcher_menu.py
# - _run_git_reset_resource -> launcher_reset.py
# - _show_gitpy_resources -> launcher_diagnostics.py
# - _run_branch_center -> launcher_branch.py
# - _run_menu_mode -> launcher_menu.py
# - _run_auto_with_guards -> launcher_auto.py


# ============================================================================
# COMANDOS CLI (Typer app.command decorators)
# ============================================================================


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    debug: bool = typer.Option(False, "--debug", help=t("option_debug_help")),
    path: str = typer.Option(".", "--path", "-p", help=t("option_path_help")),
):
    """
    {t('app_description')}

    {t('app_auto_usage')}
    """
    ctx.obj = {"debug": debug, "path": path}

    if ctx.invoked_subcommand is not None:
        return

    if _is_interactive_terminal():
        try:
            _run_menu_mode(ctx)
            return
        except MenuDependencyError as exc:
            Console().print(f"[yellow]{exc}[/yellow]")
        except KeyboardInterrupt:
            Console().print(f"\n[yellow]{t('op_cancelled')}[/yellow]")
            raise typer.Exit()

    _show_welcome_screen()


@app.command(help=t("cmd_auto_help"))
def auto(
    ctx: typer.Context,
    no_push: bool = typer.Option(False, "--no-push", help=t("flag_no_push")),
    nobuild: bool = typer.Option(False, "--nobuild", help=t("option_nobuild_help")),
    message: Optional[str] = typer.Option(None, "--message", "-m", help=t("flag_message")),
    dry_run: bool = typer.Option(False, "--dry-run", help=t("flag_dry_run")),
    model: str = typer.Option(os.getenv("AI_PROVIDER", "auto"), "--model", help=t("flag_model")),
    debug: bool = typer.Option(False, "--debug", help=t("option_debug_help")),
    yes: bool = typer.Option(False, "--yes", "-y", help=t("flag_yes")),
    branch: Optional[str] = typer.Option(None, "--branch", "-b", help=t("option_branch_help")),
):
    """
    Modo Autonomo: Analisa mudancas, gera commit e faz push.
    """
    options = AutoOptions(
        no_push=no_push,
        nobuild=nobuild,
        message=message,
        dry_run=dry_run,
        model=model,
        debug=debug,
        yes=yes,
        branch=branch,
    )
    _run_auto_with_guards(ctx, options, confirm_fn=typer.confirm)


@app.command(help=t("cmd_menu_help"))
def menu(ctx: typer.Context):
    """
    Modo interativo guiado por menus (InquirerPy).
    """
    try:
        _run_menu_mode(ctx)
    except MenuDependencyError as exc:
        Console().print(f"[red]{exc}[/red]")
        raise typer.Exit(1)
    except KeyboardInterrupt:
        Console().print(f"\n[yellow]{t('op_cancelled')}[/yellow]")
        raise typer.Exit()


@app.command()
def check_ai(ctx: typer.Context):
    """
    Diagnostico de IA: Testa a conectividade e configuracao de todos os provedores.
    """
    _ = ctx
    _run_check_ai_diagnostics()


if __name__ == "__main__":
    app()
