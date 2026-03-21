"""
Branch Center - Gerenciamento de branches do GitPy.
"""
import subprocess

import typer
from rich.console import Console
from rich.panel import Panel

from vibe_core import kernel
from i18n import t
from launcher_shared import run_async, _resolve_repo_path
from launcher_menu import (
    _render_menu_header,
    _pause_menu,
    _inquirer_select,
    _inquirer_text,
    _inquirer_confirm,
    _get_menu_repo_status,
)


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
