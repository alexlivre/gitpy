"""
Menu interativo do GitPy (InquirerPy).
"""
import os
from typing import Optional

import typer
from rich import box
from rich.console import Console
from rich.panel import Panel

from i18n import t
from navigation_stack import get_nav_stack


class MenuDependencyError(RuntimeError):
    """Raised when the interactive menu dependency is unavailable."""


def _load_inquirer():
    try:
        from InquirerPy import inquirer

        return inquirer
    except Exception as exc:
        raise MenuDependencyError(t("menu_dependency_missing")) from exc


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


def _inquirer_checkbox(message: str, choices, default=None, **kwargs):
    inquirer = _load_inquirer()
    kwargs.setdefault("instruction", t("menu_instruction_checkbox"))
    kwargs.setdefault("style", _inquirer_style())
    return inquirer.checkbox(message=message, choices=choices, default=default, **kwargs).execute()


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


def _collect_auto_options_from_menu(ctx: typer.Context):
    from launcher import AutoOptions

    default_path = (ctx.obj or {}).get("path", ".")
    
    # Verifica se o caminho atual já é um repositório Git
    # Se sim, pula a seleção de caminho e usa o diretório atual
    import subprocess
    try:
        git_check = subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            cwd=default_path,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        is_git_repo = git_check.returncode == 0
    except Exception:
        is_git_repo = False
    
    if not is_git_repo:
        # Apenas mostra a seleção de caminho se não estiver em um repo Git
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
    else:
        # Já está em um repo Git, usa o caminho atual diretamente
        chosen_path = default_path

    default_model = os.getenv("AI_PROVIDER", "auto")
    model_choices = ["auto", "openrouter", "groq", "openai", "gemini", "ollama"]
    if default_model not in model_choices:
        default_model = "auto"

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

    # Coleta as opções booleanas usando checkboxes
    debug_default = (ctx.obj or {}).get("debug", False)
    boolean_options = _inquirer_checkbox(
        t("menu_prompt_boolean_options"),
        choices=[
            {"name": t("menu_prompt_dry_run"), "value": "dry_run"},
            {"name": t("menu_prompt_no_push"), "value": "no_push"},
            {"name": t("menu_prompt_nobuild"), "value": "nobuild"},
            {"name": t("menu_prompt_debug"), "value": "debug"},
            {"name": t("menu_prompt_yes"), "value": "yes"},
        ],
        default=["debug"] if debug_default else [],
        qmark="⚙",
    )

    options = AutoOptions(
        dry_run="dry_run" in boolean_options,
        no_push="no_push" in boolean_options,
        nobuild="nobuild" in boolean_options,
        debug="debug" in boolean_options,
        yes="yes" in boolean_options,
        model=model,
        message=message or None,
        branch=branch or None,
    )

    if not ctx.obj:
        ctx.obj = {}
    ctx.obj["path"] = chosen_path or default_path
    return options


def _collect_reset_options_from_menu():
    from launcher import ResetOptions

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


def _run_menu_mode(ctx: typer.Context) -> None:
    from launcher import _is_interactive_terminal, _resolve_repo_path
    from launcher_branch import _run_branch_center
    from launcher_diagnostics import _run_check_ai_diagnostics, _show_gitpy_resources
    from launcher_reset import _run_git_reset_resource
    from launcher_auto import _run_auto_with_guards

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


def _get_menu_repo_status(ctx: typer.Context) -> Optional[str]:
    """Retorna linha de status do repo atual para o header do menu."""
    import subprocess
    from launcher import _resolve_repo_path

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
