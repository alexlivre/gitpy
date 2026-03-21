"""
Central module for GitPy Launcher functionality.
"""
import asyncio
import os
import subprocess
import sys
from dataclasses import dataclass
from typing import Callable, Optional

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

from vibe_core import kernel
from i18n import t
from navigation_stack import get_nav_stack


class MenuDependencyError(RuntimeError):
    """Raised when the interactive menu dependency is unavailable."""


@dataclass
class AutoOptions:
    wip: bool = False
    no_push: bool = False
    nobuild: bool = False
    message: Optional[str] = None
    dry_run: bool = False
    model: str = "auto"
    debug: bool = False
    yes: bool = False
    branch: Optional[str] = None


@dataclass
class ResetOptions:
    mode: str = "summary"  # summary | dry_run | full
    quiet: bool = False


# Inicializa a aplicacao Typer
app = typer.Typer(
    help=t("app_help"),
    add_completion=False,
    no_args_is_help=False,
)


def run_async(coro):
    """Auxiliar para rodar corrotinas em contexto sincrono do Typer."""
    return asyncio.run(coro)


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


def _resolve_repo_path(ctx: typer.Context) -> str:
    repo_path = "."
    if ctx.obj and "path" in ctx.obj:
        repo_path = ctx.obj.get("path", ".")
    elif "path" in ctx.params:
        repo_path = ctx.params.get("path", ".")

    if repo_path == ".":
        return os.getcwd()
    return repo_path


def _load_inquirer():
    try:
        from InquirerPy import inquirer

        return inquirer
    except Exception as exc:
        raise MenuDependencyError(t("menu_dependency_missing")) from exc


def _inquirer_select(message: str, choices, default=None, **kwargs):
    inquirer = _load_inquirer()
    kwargs.setdefault("instruction", t("menu_instruction"))
    kwargs.setdefault("style", _inquirer_style())
    return inquirer.select(message=message, choices=choices, default=default, **kwargs).execute()


def _inquirer_text(message: str, default: str = "", **kwargs) -> str:
    inquirer = _load_inquirer()
    kwargs.setdefault("qmark", "✎")
    kwargs.setdefault("instruction", t("menu_instruction_text"))
    kwargs.setdefault("style", _inquirer_style())
    return inquirer.text(message=message, default=default, **kwargs).execute()


def _inquirer_confirm(message: str, default: bool = False, **kwargs) -> bool:
    kwargs.setdefault("pointer", "❯")
    kwargs.setdefault("qmark", "⚙")
    kwargs.setdefault("amark", "✓")
    kwargs.setdefault("instruction", t("menu_instruction"))
    kwargs.setdefault("style", _inquirer_style())
    kwargs.setdefault("cycle", True)

    return _inquirer_select(
        message=message,
        choices=[
            {"name": t("menu_yes_option"), "value": True},
            {"name": t("menu_no_option"), "value": False},
        ],
        default=default,
        **kwargs,
    )


def _menu_confirm(message: str) -> bool:
    return _inquirer_confirm(message, default=False)


def _inquirer_style():
    from InquirerPy import get_style

    return get_style(
        {
            "questionmark": "#ff2c6d bold",
            "question": "#d9e7ff bold",
            "answer": "#7dd3fc bold",
            "pointer": "#22d3ee bold",
            "highlighted": "#22d3ee bold",
            "selected": "#4ade80 bold",
            "separator": "#64748b",
            "instruction": "#94a3b8",
        },
        style_override=False,
    )


def _get_menu_repo_status(ctx: typer.Context) -> Optional[str]:
    """Retorna linha de status do repo atual para o header do menu."""
    repo_path = _resolve_repo_path(ctx)
    try:
        top_res = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if top_res.returncode != 0:
            return None

        top_level = top_res.stdout.strip()
        if not top_level:
            return None

        repo_name = os.path.basename(top_level.rstrip("\\/")) or top_level
        branch_res = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        branch = branch_res.stdout.strip() if branch_res.returncode == 0 else ""
        if not branch:
            head_res = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            branch = head_res.stdout.strip() if head_res.returncode == 0 else ""
        if not branch:
            branch = "HEAD"

        return t("menu_repo_status", repo=repo_name, branch=branch)
    except Exception:
        return None


def _render_menu_header(subtitle_key: str = "menu_subtitle_main", repo_status: Optional[str] = None) -> None:
    from rich.text import Text

    console = Console()
    console.clear()

    logo = Text(
        "\n  ██████╗ ██╗████████╗██████╗ ██╗   ██╗\n"
        " ██╔════╝ ██║╚══██╔══╝██╔══██╗╚██╗ ██╔╝\n"
        " ██║  ███╗██║   ██║   ██████╔╝ ╚████╔╝\n"
        " ██║   ██║██║   ██║   ██╔═══╝   ╚██╔╝\n"
        " ╚██████╔╝██║   ██║   ██║        ██║\n"
        "  ╚═════╝ ╚═╝   ╚═╝   ╚═╝        ╚═╝\n",
        style="bold #c084fc",
    )
    subtitle = Text(f"  {t(subtitle_key)}", style="bold #22d3ee")

    # Breadcrumb da pilha de navegação
    nav_stack = get_nav_stack()
    breadcrumb_text = ""
    if not nav_stack.is_empty():
        breadcrumb = nav_stack.get_breadcrumb(t("breadcrumb_separator"))
        breadcrumb_text = f"\n  [dim cyan]📍 {breadcrumb}[/dim cyan]"

    repo_line = Text(
        f"\n  {repo_status}",
        style="bold #facc15",
    ) if repo_status else Text("")
    version = Text("GitPy v1.0", style="bold #a78bfa")

    body = Text.assemble(logo, subtitle, Text(breadcrumb_text), repo_line)
    panel = Panel(
        body,
        title=version,
        subtitle=Text("Powered by Vibe Engineering", style="#a78bfa"),
        border_style="#a78bfa",
        box=box.DOUBLE,
        padding=(0, 1),
    )
    console.print(panel)


def _pause_menu() -> None:
    console = Console()
    console.print(f"\n[dim]{t('menu_press_enter')}[/dim]")
    try:
        console.input()
    except (EOFError, KeyboardInterrupt):
        return


def _run_check_ai_diagnostics() -> None:
    from rich.table import Table

    console = Console()
    providers = ["openrouter", "groq", "openai", "gemini", "ollama"]

    table = Table(title=t("diag_title"), box=box.ROUNDED, border_style="purple")
    table.add_column(t("col_provider"), style="cyan")
    table.add_column(t("col_config"), justify="center")
    table.add_column(t("col_status"), justify="center")
    table.add_column(t("col_details"), style="dim")

    async def run_diagnostics():
        results = []
        for p in providers:
            key_res = await kernel.run(
                "security/sec-keyring", {"action": "get", "service": f"{p}_api_key"}
            )
            has_key = key_res.get("success", False)

            if not has_key and p != "ollama":
                results.append((p.upper(), "🟡", "-", t("error_no_key")))
                continue

            config_status = t("config_local") if p == "ollama" else t("config_ok")

            test_prompt = "Responda apenas 'PONG'."
            try:
                test_res = await kernel.run(
                    f"ai/ai-{p}",
                    {
                        "prompt": test_prompt,
                        "system_instruction": "Você é um testador. Responda apenas PONG.",
                        "max_tokens": 10,
                    },
                    timeout=15,
                )

                if test_res.get("error"):
                    status = "🔴"
                    details = test_res.get("message", "Erro desconhecido")
                else:
                    status = "🟢"
                    details = t("status_pinging", model=test_res.get("model_used", "default"))
            except Exception as exc:
                status = "🔴"
                details = str(exc)

            results.append((p.upper(), config_status, status, details))
        return results

    with console.status(f"[bold purple]{t('running_diag')}", spinner="earth"):
        diag_results = run_async(run_diagnostics())
        for row in diag_results:
            table.add_row(*row)

    console.print(table)
    console.print(f"\n[dim]{t('diag_hint')}[/dim]")


def _collect_auto_options_from_menu(ctx: typer.Context) -> AutoOptions:
    default_path = (ctx.obj or {}).get("path", ".")
    default_model = os.getenv("AI_PROVIDER", "auto")
    model_choices = ["auto", "openrouter", "groq", "openai", "gemini", "ollama"]
    if default_model not in model_choices:
        default_model = "auto"

    path_mode = _inquirer_select(
        t("menu_prompt_path_mode"),
        choices=[
            {"name": t("menu_path_mode_current", path=default_path), "value": "current"},
            {"name": t("menu_path_mode_custom"), "value": "custom"},
            {"name": t("menu_auto_back"), "value": "back"},
        ],
        default="current",
        pointer="❯",
        qmark="⚙",
        amark="✓",
        cycle=True,
    )

    if path_mode == "back":
        return None

    if path_mode == "custom":
        chosen_path = _inquirer_text(
            t("menu_prompt_path_custom"),
            default=default_path,
        ).strip()
        if chosen_path.lower() == "back":
            return None
    else:
        chosen_path = default_path

    model = _inquirer_select(
        t("menu_prompt_model"),
        choices=[
            {"name": "auto", "value": "auto"},
            {"name": "openrouter", "value": "openrouter"},
            {"name": "groq", "value": "groq"},
            {"name": "openai", "value": "openai"},
            {"name": "gemini", "value": "gemini"},
            {"name": "ollama", "value": "ollama"},
            {"name": t("menu_auto_back"), "value": "back"},
        ],
        default=default_model,
        pointer="❯",
        qmark="⚙",
        amark="✓",
        cycle=True,
    )

    if model == "back":
        return None
    message = _inquirer_text(t("menu_prompt_message"), default="").strip()
    if message.lower() == "back":
        return None
    branch = _inquirer_text(t("menu_prompt_branch"), default="").strip()
    if branch.lower() == "back":
        return None

    options = AutoOptions(
        wip=_inquirer_confirm(
            t("menu_prompt_wip"),
            default=False,
            qmark="⚙",
        ),
        dry_run=_inquirer_confirm(
            t("menu_prompt_dry_run"),
            default=False,
            qmark="⚙",
        ),
        no_push=_inquirer_confirm(
            t("menu_prompt_no_push"),
            default=False,
            qmark="⚙",
        ),
        nobuild=_inquirer_confirm(
            t("menu_prompt_nobuild"),
            default=False,
            qmark="⚙",
        ),
        debug=_inquirer_confirm(
            t("menu_prompt_debug"),
            default=(ctx.obj or {}).get("debug", False),
            qmark="⚙",
        ),
        yes=_inquirer_confirm(
            t("menu_prompt_yes"),
            default=False,
            qmark="⚙",
        ),
        model=model,
        message=message or None,
        branch=branch or None,
    )

    if not ctx.obj:
        ctx.obj = {}
    ctx.obj["path"] = chosen_path or default_path
    return options


def _collect_reset_options_from_menu() -> Optional[ResetOptions]:
    mode = _inquirer_select(
        t("menu_reset_mode_prompt"),
        choices=[
            {"name": t("menu_reset_mode_summary"), "value": "summary"},
            {"name": t("menu_reset_mode_dry_run"), "value": "dry_run"},
            {"name": t("menu_reset_mode_full"), "value": "full"},
            {"name": t("menu_action_back"), "value": "back"},
        ],
        default="summary",
        pointer="❯",
        qmark="⚙",
        amark="✓",
        cycle=True,
    )

    if mode == "back":
        return None

    quiet = _inquirer_confirm(
        t("menu_reset_quiet_prompt"),
        default=False,
        qmark="⚙",
    )
    return ResetOptions(mode=mode, quiet=quiet)


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


def _show_gitpy_resources() -> None:
    from rich.table import Table

    console = Console()
    table = Table(title=t("menu_resources_title"), box=box.ROUNDED, border_style="bright_cyan")
    table.add_column(t("menu_resources_col_resource"), style="cyan", no_wrap=True)
    table.add_column(t("menu_resources_col_access"), style="magenta")
    table.add_column(t("menu_resources_col_notes"), style="dim")

    table.add_row(
        t("menu_resources_auto_name"),
        "auto + menu",
        t("menu_resources_auto_notes"),
    )
    table.add_row(
        t("menu_resources_branch_name"),
        "branch center + --branch",
        t("menu_resources_branch_notes"),
    )
    table.add_row(
        t("menu_resources_diag_name"),
        "check-ai + menu",
        t("menu_resources_diag_notes"),
    )
    table.add_row(
        t("menu_resources_reset_name"),
        "git_reset_to_github.py + menu",
        t("menu_resources_reset_notes"),
    )
    table.add_row(
        t("menu_resources_wrappers_name"),
        "gitpy.cmd / pygit.cmd",
        t("menu_resources_wrappers_notes"),
    )
    table.add_row(
        t("menu_resources_global_name"),
        "--debug / --path",
        t("menu_resources_global_notes"),
    )
    table.add_row(
        t("menu_resources_i18n_name"),
        "LANGUAGE / COMMIT_LANGUAGE",
        t("menu_resources_i18n_notes"),
    )

    console.print(table)
    console.print(f"[dim]{t('menu_resources_hint')}[/dim]")


def _run_branch_center(ctx: typer.Context) -> None:
    console = Console()
    repo_path = _resolve_repo_path(ctx)

    while True:
        _render_menu_header("menu_subtitle_branch", repo_status=_get_menu_repo_status(ctx))
        action = _inquirer_select(
            t("menu_branch_prompt"),
            choices=[
                {"name": t("menu_branch_action_current"), "value": "current"},
                {"name": t("menu_branch_action_list"), "value": "list"},
                {"name": t("menu_branch_action_create_switch"), "value": "create_switch"},
                {"name": t("menu_branch_action_switch"), "value": "switch"},
                {"name": t("menu_branch_action_validate"), "value": "validate"},
                {"name": t("menu_action_back"), "value": "back"},
            ],
            default="current",
            pointer="❯",
            qmark="🌿",
            amark="✓",
            cycle=True,
        )

        if action == "back":
            return

        if action == "current":
            current_res = run_async(
                kernel.run("core/git-branch", {"action": "current", "repo_path": repo_path})
            )
            if current_res.get("success"):
                console.print(
                    Panel(
                        f"[bold green]{current_res.get('current_branch', 'unknown')}[/bold green]",
                        title=t("menu_branch_current_title"),
                        border_style="green",
                    )
                )
            else:
                console.print(f"[red]{current_res.get('error', t('menu_branch_generic_error'))}[/red]")
            _pause_menu()
            continue

        if action == "list":
            result = subprocess.run(
                ["git", "branch", "-a"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            if result.returncode == 0:
                content = result.stdout.strip() or t("menu_branch_list_empty")
                console.print(
                    Panel(
                        f"[white]{content}[/white]",
                        title=t("menu_branch_list_title"),
                        border_style="cyan",
                    )
                )
            else:
                console.print(f"[red]{result.stderr.strip() or t('menu_branch_generic_error')}[/red]")
            _pause_menu()
            continue

        branch_name = _inquirer_text(
            t("menu_branch_name_prompt"),
            default="",
            qmark="🌿",
        ).strip()

        if branch_name.lower() == "back":
            continue

        validation = run_async(
            kernel.run(
                "core/git-branch",
                {"action": "validate", "branch_name": branch_name, "repo_path": repo_path},
            )
        )
        if not validation.get("valid"):
            console.print(
                Panel(
                    f"[bold red]{validation.get('error', t('menu_branch_generic_error'))}[/bold red]",
                    title=t("menu_branch_validate_fail_title"),
                    border_style="red",
                )
            )
            _pause_menu()
            continue

        if action == "validate":
            console.print(
                Panel(
                    f"[bold green]{t('menu_branch_validate_ok')}[/bold green]",
                    title=t("menu_branch_validate_ok_title"),
                    border_style="green",
                )
            )
            _pause_menu()
            continue

        exists = run_async(
            kernel.run(
                "core/git-branch",
                {"action": "exists", "branch_name": branch_name, "repo_path": repo_path},
            )
        ).get("exists", False)

        if action == "switch":
            if not exists:
                console.print(
                    Panel(
                        f"[bold red]{t('menu_branch_switch_missing', branch=branch_name)}[/bold red]",
                        border_style="red",
                    )
                )
                _pause_menu()
                continue

            switch_res = run_async(
                kernel.run(
                    "core/git-branch",
                    {"action": "switch", "branch_name": branch_name, "repo_path": repo_path},
                )
            )
            if switch_res.get("success"):
                console.print(f"[bold green]{t('menu_branch_switch_ok', branch=branch_name)}[/bold green]")
            else:
                console.print(f"[bold red]{switch_res.get('error', t('menu_branch_generic_error'))}[/bold red]")
            _pause_menu()
            continue

        # action == create_switch
        if exists:
            if not _inquirer_confirm(
                t("menu_branch_exists_switch_confirm", branch=branch_name),
                default=True,
                qmark="🌿",
            ):
                console.print(f"[yellow]{t('op_cancelled')}[/yellow]")
                _pause_menu()
                continue
        else:
            create_res = run_async(
                kernel.run(
                    "core/git-branch",
                    {"action": "create", "branch_name": branch_name, "repo_path": repo_path},
                )
            )
            if not create_res.get("success"):
                console.print(f"[bold red]{create_res.get('error', t('menu_branch_generic_error'))}[/bold red]")
                _pause_menu()
                continue

        switch_res = run_async(
            kernel.run(
                "core/git-branch",
                {"action": "switch", "branch_name": branch_name, "repo_path": repo_path},
            )
        )
        if switch_res.get("success"):
            console.print(f"[bold green]{t('menu_branch_switch_ok', branch=branch_name)}[/bold green]")
        else:
            console.print(f"[bold red]{switch_res.get('error', t('menu_branch_generic_error'))}[/bold red]")
        _pause_menu()


def _run_menu_mode(ctx: typer.Context) -> None:
    if not _is_interactive_terminal():
        Console().print(f"[yellow]{t('menu_requires_tty')}[/yellow]")
        raise typer.Exit(1)

    console = Console()
    nav_stack = get_nav_stack()

    # Inicializa pilha com Raiz se estiver vazia
    if nav_stack.is_empty():
        nav_stack.push("root", "menu_subtitle_main", t("breadcrumb_root"))

    while True:
        _render_menu_header(repo_status=_get_menu_repo_status(ctx))
        action = _inquirer_select(
            t("menu_main_prompt"),
            choices=[
                {"name": f"{t('menu_action_auto')}  [dim]{t('menu_action_auto_desc')}[/dim]", "value": "auto"},
                {"name": f"{t('menu_action_branch')}  [dim]{t('menu_action_branch_desc')}[/dim]", "value": "branch"},
                {"name": f"{t('menu_action_check_ai')}  [dim]{t('menu_action_check_ai_desc')}[/dim]", "value": "check_ai"},
                {"name": f"{t('menu_action_reset')}  [dim]{t('menu_action_reset_desc')}[/dim]", "value": "reset"},
                {"name": f"{t('menu_action_resources')}  [dim]{t('menu_action_resources_desc')}[/dim]", "value": "resources"},
                {"name": t("menu_action_exit"), "value": "exit"},
            ],
            default="auto",
            pointer="❯",
            qmark="✔",
            amark="✓",
            cycle=True,
        )

        if action == "exit":
            nav_stack.clear()
            console.print(f"[yellow]{t('menu_goodbye')}[/yellow]")
            return

        if action == "branch":
            nav_stack.push("branch", "menu_subtitle_branch", t("menu_subtitle_branch"))
            _run_branch_center(ctx)
            nav_stack.pop()
            continue

        if action == "check_ai":
            nav_stack.push("check_ai", "menu_subtitle_diag", t("menu_subtitle_diag"))
            _render_menu_header("menu_subtitle_diag", repo_status=_get_menu_repo_status(ctx))
            console.print(f"[cyan]{t('menu_running_check_ai')}[/cyan]")
            _run_check_ai_diagnostics()
            nav_stack.pop()
            _pause_menu()
            continue

        if action == "reset":
            nav_stack.push("reset", "menu_subtitle_reset", t("menu_subtitle_reset"))
            _render_menu_header("menu_subtitle_reset", repo_status=_get_menu_repo_status(ctx))
            user_completed = _run_git_reset_resource(ctx)
            nav_stack.pop()
            if user_completed:
                _pause_menu()
            continue

        if action == "resources":
            nav_stack.push("resources", "menu_subtitle_resources", t("menu_subtitle_resources"))
            _render_menu_header("menu_subtitle_resources", repo_status=_get_menu_repo_status(ctx))
            _show_gitpy_resources()
            nav_stack.pop()
            _pause_menu()
            continue

        # action == auto
        nav_stack.push("auto", "menu_subtitle_auto", t("menu_subtitle_auto"))
        _render_menu_header("menu_subtitle_auto", repo_status=_get_menu_repo_status(ctx))
        options = _collect_auto_options_from_menu(ctx)
        if options is None:
            # Usuário escolheu voltar
            nav_stack.pop()
            continue
        console.print(f"[cyan]{t('menu_running_auto')}[/cyan]")
        _run_auto_with_guards(ctx, options, confirm_fn=_menu_confirm)
        nav_stack.pop()
        _pause_menu()


def _run_auto_with_guards(
    ctx: typer.Context,
    options: AutoOptions,
    confirm_fn: Callable[[str], bool],
) -> None:
    console = Console()
    repo_path = _resolve_repo_path(ctx)

    if options.branch:
        validation_res = run_async(
            kernel.run(
                "core/git-branch",
                {"action": "validate", "branch_name": options.branch, "repo_path": repo_path},
            )
        )
        if not validation_res.get("valid"):
            console.print(
                Panel(
                    f"[bold red]{t('branch_invalid_name', branch=options.branch)}[/bold red]\n"
                    f"{validation_res.get('error')}",
                    title="❌ Erro de Validacao",
                    border_style="red",
                )
            )
            raise typer.Exit(1)

        exists_res = run_async(
            kernel.run(
                "core/git-branch",
                {"action": "exists", "branch_name": options.branch, "repo_path": repo_path},
            )
        )

        if exists_res.get("exists"):
            console.print(f"[bold yellow]{t('branch_exists', branch=options.branch)}[/bold yellow]")
            action_msg = t("branch_switching", branch=options.branch)
        else:
            action_msg = t("branch_creating", branch=options.branch)

        with console.status(f"[bold cyan]{action_msg}[/bold cyan]", spinner="dots"):
            if exists_res.get("exists"):
                switch_res = run_async(
                    kernel.run(
                        "core/git-branch",
                        {"action": "switch", "branch_name": options.branch, "repo_path": repo_path},
                    )
                )
            else:
                create_res = run_async(
                    kernel.run(
                        "core/git-branch",
                        {"action": "create", "branch_name": options.branch, "repo_path": repo_path},
                    )
                )
                if create_res.get("success"):
                    switch_res = run_async(
                        kernel.run(
                            "core/git-branch",
                            {"action": "switch", "branch_name": options.branch, "repo_path": repo_path},
                        )
                    )
                else:
                    switch_res = {"success": False, "error": create_res.get("error")}

        if not switch_res.get("success"):
            console.print(
                Panel(
                    f"[bold red]{t('branch_error', branch=options.branch, error=switch_res.get('error'))}[/bold red]",
                    title="❌ Erro na Branch",
                    border_style="red",
                )
            )
            raise typer.Exit(1)

        console.print(f"[bold green]{t('branch_success', branch=options.branch)}[/bold green]")

    try:
        run_async(kernel.run("tool/tool-stealth", {"action": "restore", "repo_path": repo_path}))
    except Exception:
        pass

    stash_res = run_async(kernel.run("tool/tool-stealth", {"action": "stash", "repo_path": repo_path}))
    if not stash_res.get("success"):
        console.print(
            Panel(
                f"[bold red]{t('stealth_stash_failed')}[/bold red]\n"
                f"{stash_res.get('error')}\n"
                f"[yellow]{t('stealth_abort_prevent_leak')}[/yellow]",
                title="🛡️ Stealth Mode Abort",
                border_style="red",
            )
        )
        raise typer.Exit(1)

    hidden_count = len(stash_res.get("files_moved", []))
    if hidden_count > 0:
        console.print(f"[bold magenta]{t('stealth_active', count=hidden_count)}[/bold magenta]")

    try:
        _auto_impl(ctx, options=options, confirm_fn=confirm_fn)
    finally:
        restore_res = run_async(
            kernel.run("tool/tool-stealth", {"action": "restore", "repo_path": repo_path})
        )
        if not restore_res.get("success"):
            console.print(f"[bold red]{t('stealth_restore_warn')}[/bold red]")
            console.print(f"Details: {restore_res.get('details')}")
        elif restore_res.get("restored_files"):
            console.print(
                f"[dim]{t('stealth_restored', count=len(restore_res.get('restored_files')))}[/dim]"
            )


def _auto_impl(
    ctx: typer.Context,
    options: AutoOptions,
    confirm_fn: Callable[[str], bool],
) -> None:
    """
    Modo Autonomo: Analisa mudancas, gera commit e faz push.
    """
    console = Console()
    repo_path = _resolve_repo_path(ctx)
    global_debug = (ctx.obj or {}).get("debug", False)
    kernel.debug_mode = options.debug or global_debug

    _ = options.wip  # Mantido por compatibilidade de interface.

    model = options.model
    if model == "auto":
        with console.status(f"[bold cyan]{t('detecting_ai')}", spinner="dots"):
            detected_provider = "openai"

            openrouter_key = run_async(
                kernel.run("security/sec-keyring", {"action": "get", "service": "openrouter_api_key"})
            ).get("value")
            if openrouter_key:
                detected_provider = "openrouter"
            else:
                groq_key = run_async(
                    kernel.run("security/sec-keyring", {"action": "get", "service": "groq_api_key"})
                ).get("value")
                if groq_key:
                    detected_provider = "groq"
                else:
                    openai_key = run_async(
                        kernel.run("security/sec-keyring", {"action": "get", "service": "openai_api_key"})
                    ).get("value")
                    if openai_key:
                        detected_provider = "openai"
                    else:
                        gemini_key = run_async(
                            kernel.run("security/sec-keyring", {"action": "get", "service": "gemini_api_key"})
                        ).get("value")
                        if gemini_key:
                            detected_provider = "gemini"

        model = detected_provider
        console.print(f"[bold cyan]{t('ai_provider_label', model=model.upper())}[/bold cyan]")

    with console.status(f"[bold green]{t('checking_ignore')}", spinner="dots"):
        ignore_res = run_async(kernel.run("tool/tool-ignore", {"action": "scan", "repo_path": repo_path}))
        suggestions = ignore_res.get("suggestions", [])

    if suggestions:
        console.print(
            Panel(
                f"[yellow]{t('ignore_detected_files')}[/yellow]\n"
                f"[bold white]{', '.join(suggestions)}[/bold white]",
                title=t("ignore_suggestion_title"),
                border_style="yellow",
            )
        )
        if options.yes or confirm_fn(t("ignore_confirm")):
            for pat in suggestions:
                run_async(kernel.run("tool/tool-ignore", {"action": "add", "pattern": pat, "repo_path": repo_path}))
            console.print(f"[green]{t('ignore_updated_restart')}[/green]")

    with console.status(f"[bold green]{t('analyzing_repo')}", spinner="dots"):
        scan_res = run_async(kernel.run("core/git-scanner", {"repo_path": repo_path}))

    if not scan_res.get("is_repo"):
        run_async(kernel.run("cli/cli-renderer", {"action": "error", "message": t("error_not_repo")}))
        raise typer.Exit(1)

    if not scan_res.get("has_changes"):
        console.print(f"[yellow]{t('clean_tree')}[/yellow]")
        return

    files_changed = scan_res.get("files_changed", [])
    if files_changed:
        sanitizer_res = run_async(kernel.run("security/sec-sanitizer", {"file_paths": files_changed}))
        violations = sanitizer_res.get("violations", 0)

        if violations > 0:
            blocked = sanitizer_res.get("blocked_files", [])
            console.print(
                Panel(
                    f"[bold red]{t('security_block_activated')}[/bold red]\n\n"
                    f"{t('security_files_detected', count=violations)}\n"
                    f"{', '.join(blocked)}\n\n"
                    f"[yellow]{t('security_action_blocked')}[/yellow]",
                    title="🛡️ Security Blocklist",
                    border_style="red",
                )
            )
            raise typer.Exit(1)

    diff_data = scan_res.get("diff_data", {})
    diff_mode = diff_data.get("mode", "none")

    if diff_mode == "ref":
        diff_content = diff_data.get("preview", "")
        console.print(f"[bold yellow]{t('vibe_vault_activated')}[/bold yellow]")
    else:
        diff_content = diff_data.get("content", "")

    run_async(kernel.run("cli/cli-renderer", {"action": "diff_panel", "data": {"diff": diff_content[:2000]}}))

    if not options.yes and not confirm_fn(t("confirm_gen_commit")):
        typer.echo(t("op_cancelled"))
        raise typer.Exit()

    with console.status(f"[bold purple]{t('brain_thinking', model=model)}", spinner="bouncingBall"):
        raw_commit_lang = os.getenv("COMMIT_LANGUAGE", "en")
        commit_lang = raw_commit_lang.split("#")[0].strip().lower()

        brain_res = run_async(
            kernel.run(
                "ai/ai-brain",
                {
                    "diff": diff_content,
                    "repo_path": repo_path,
                    "hint": options.message,
                    "provider": model,
                    "commit_lang": commit_lang,
                    "is_truncated": (diff_mode == "ref"),
                },
            )
        )

    if not brain_res.get("success"):
        run_async(
            kernel.run(
                "cli/cli-renderer",
                {"action": "error", "message": t("error_ai", message=brain_res.get("message"))},
            )
        )
        raise typer.Exit(1)

    commit_msg = brain_res.get("commit_message")
    if options.nobuild:
        commit_msg = f"[CI Skip] {commit_msg}"

    console.print(Panel(f"[bold white]{commit_msg}[/bold white]", title=t("generated_commit_title"), border_style="purple"))

    if options.dry_run:
        console.print(f"[cyan]{t('dry_run_commit')}[/cyan]")
        return

    if options.yes or confirm_fn(t("confirm_exec_commit")):
        with console.status(f"[bold blue]{t('committing_pushing')}", spinner="line"):
            run_async(kernel.run("core/git-executor", {"repo_path": repo_path, "command": "add -A"}))

            safe_msg = commit_msg.replace("'", '"')
            exec_res = run_async(
                kernel.run("core/git-executor", {"repo_path": repo_path, "command": f"commit -m '{safe_msg}'"})
            )

            if exec_res.get("success"):
                console.print(f"[green]{t('commit_success')}[/green]")

                if not options.no_push:
                    console.print(f"[bold blue]{t('pushing_remote')}[/bold blue]")
                    push_res = run_async(kernel.run("core/git-executor", {"repo_path": repo_path, "command": "push"}))
                    if push_res.get("success"):
                        run_async(kernel.run("cli/cli-renderer", {"action": "success", "message": t("push_success")}))
                    else:
                        console.print(f"[bold red]{t('push_failed_healer')}[/bold red]")
                        heal_res = run_async(
                            kernel.run(
                                "core/git-healer",
                                {
                                    "repo_path": repo_path,
                                    "failed_command": "git push",
                                    "error_output": push_res.get("stderr"),
                                    "provider": model,
                                    "max_retries": 10,
                                },
                            )
                        )

                        if heal_res.get("success"):
                            run_async(
                                kernel.run(
                                    "cli/cli-renderer",
                                    {
                                        "action": "success",
                                        "message": t("healer_saved_day", message=heal_res.get("message")),
                                    },
                                )
                            )
                        else:
                            run_async(
                                kernel.run(
                                    "cli/cli-renderer",
                                    {
                                        "action": "error",
                                        "message": t("healer_failed", message=heal_res.get("message")),
                                    },
                                )
                            )
            else:
                run_async(
                    kernel.run(
                        "cli/cli-renderer",
                        {"action": "error", "message": t("commit_failed", error=exec_res.get("stderr"))},
                    )
                )
    else:
        console.print(f"[yellow]{t('op_cancelled')}[/yellow]")


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
    wip: bool = typer.Option(False, "--wip", help=t("option_wip_help")),
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
        wip=wip,
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
