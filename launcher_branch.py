"""Branch Center - Gerenciamento de branches do GitPy."""

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
    _inquirer_checkbox,
    _inquirer_text,
    _inquirer_confirm,
    _get_menu_repo_status,
)


def _run_branch_center(ctx: typer.Context) -> None:
    console = Console()
    repo_path = _resolve_repo_path(ctx)

    def _load_branch_list():
        return run_async(kernel.run("core/git-branch", {"action": "list", "repo_path": repo_path}))

    def _build_branch_choices(branch_names, current_branch, include_current=True):
        choices = []
        for name in branch_names:
            if not include_current and name == current_branch:
                continue
            label = f"{name} [dim]({t('menu_branch_current_marker')})[/dim]" if name == current_branch else name
            choices.append({"name": label, "value": name})
        return choices

    def _run_bulk_action(action: str):
        listed = _load_branch_list()
        if not listed.get("success"):
            console.print(f"[red]{listed.get('error', t('menu_branch_generic_error'))}[/red]")
            _pause_menu()
            return

        current_branch = listed.get("current_branch", "")
        local_branches = listed.get("local_branches", [])

        if action == "bulk_delete":
            branch_choices = _build_branch_choices(local_branches, current_branch, include_current=False)
            prompt = t("menu_branch_bulk_delete_prompt")
            kernel_action = "delete_multiple"
            payload_extra = {"force": False}
        else:
            branch_choices = _build_branch_choices(local_branches, current_branch, include_current=True)
            prompt = t("menu_branch_bulk_push_prompt")
            confirm_msg = t("menu_branch_bulk_push_confirm")
            kernel_action = "push_branch"
            payload_extra = {"remote": "origin"}

        if not branch_choices:
            console.print(f"[yellow]{t('menu_branch_bulk_empty')}[/yellow]")
            _pause_menu()
            return

        selected = _inquirer_checkbox(
            prompt,
            choices=branch_choices,
            default=[],
            pointer="❯",
            qmark="🌿",
            cycle=True,
        )
        if not selected:
            console.print(f"[yellow]{t('op_cancelled')}[/yellow]")
            _pause_menu()
            return

        if action == "bulk_delete":
            # New confirmation flow for bulk delete
            payload = {
                "action": kernel_action,
                "branches_to_delete": selected,
                "repo_path": repo_path,
                **payload_extra,
            }
            result = run_async(kernel.run("core/git-branch", payload))
            
            if not result.get("success") and result.get("error") == "CONFIRMATION_REQUIRED":
                # Show confirmation code and ask for input
                confirmation_code = result.get("confirmation_code", "")
                branches_count = result.get("branches_count", len(selected))
                
                console.print(f"[bold yellow]{t('menu_branch_bulk_delete_confirmation_required', count=branches_count, code=confirmation_code)}[/bold yellow]")
                
                # Loop for code input with validation
                while True:
                    user_code = _inquirer_text(
                        t("menu_branch_bulk_delete_confirmation_prompt"),
                        qmark="🔒",
                    ).strip()
                    
                    if not user_code:
                        console.print(f"[yellow]{t('menu_branch_bulk_delete_cancelled')}[/yellow]")
                        _pause_menu()
                        return
                    
                    # Second call with confirmation code
                    payload["confirmation_code"] = user_code
                    payload["expected_code"] = confirmation_code
                    result = run_async(kernel.run("core/git-branch", payload))
                    
                    if not result.get("success") and result.get("error") == "INVALID_CONFIRMATION":
                        console.print(f"[red]{t('menu_branch_bulk_delete_confirmation_invalid')}[/red]")
                        continue
                    else:
                        break
            
            if not result.get("success"):
                error_text = result.get("message") or result.get("error") or t("menu_branch_generic_error")
                console.print(f"[red]{error_text}[/red]")
                _pause_menu()
                return
            
            # Show results for delete_multiple
            if action == "bulk_delete":
                results = result.get("results", [])
                success_count = result.get("success_count", 0)
                fail_count = result.get("fail_count", 0)
                
                for item in results:
                    if item.get("success"):
                        console.print(f"[green]{t('menu_branch_bulk_item_ok', branch=item['branch'])}[/green]")
                    else:
                        error_text = item.get("error", t("menu_branch_generic_error"))
                        console.print(f"[red]{t('menu_branch_bulk_item_fail', branch=item['branch'], error=error_text)}[/red]")
                
                console.print(
                    Panel(
                        f"[bold green]{t('menu_branch_bulk_summary_ok', count=success_count)}[/bold green]\n"
                        f"[bold red]{t('menu_branch_bulk_summary_fail', count=fail_count)}[/bold red]",
                        title=t("menu_branch_bulk_summary_title"),
                        border_style="cyan",
                    )
                )
                _pause_menu()
                return
        
        # Original flow for bulk_push
        if not _inquirer_confirm(confirm_msg, default=False, qmark="🌿"):
            console.print(f"[yellow]{t('op_cancelled')}[/yellow]")
            _pause_menu()
            return

        ok_count = 0
        fail_count = 0
        for selected_branch in selected:
            payload = {
                "action": kernel_action,
                "branch_name": selected_branch,
                "repo_path": repo_path,
                **payload_extra,
            }
            result = run_async(kernel.run("core/git-branch", payload))
            if result.get("success"):
                ok_count += 1
                console.print(f"[green]{t('menu_branch_bulk_item_ok', branch=selected_branch)}[/green]")
            else:
                fail_count += 1
                error_text = result.get("message") or result.get("error") or t("menu_branch_generic_error")
                console.print(f"[red]{t('menu_branch_bulk_item_fail', branch=selected_branch, error=error_text)}[/red]")

        console.print(
            Panel(
                f"[bold green]{t('menu_branch_bulk_summary_ok', count=ok_count)}[/bold green]\n"
                f"[bold red]{t('menu_branch_bulk_summary_fail', count=fail_count)}[/bold red]",
                title=t("menu_branch_bulk_summary_title"),
                border_style="cyan",
            )
        )
        _pause_menu()

    while True:
        _render_menu_header("menu_subtitle_branch", repo_status=_get_menu_repo_status(ctx))
        action = _inquirer_select(
            t("menu_branch_prompt"),
            choices=[
                {"name": t("menu_branch_action_current"), "value": "current"},
                {"name": t("menu_branch_action_list"), "value": "list"},
                {"name": t("menu_branch_action_create_switch"), "value": "create_switch"},
                {"name": t("menu_branch_action_switch"), "value": "switch"},
                {"name": t("menu_branch_action_bulk_delete"), "value": "bulk_delete"},
                {"name": t("menu_branch_action_bulk_push"), "value": "bulk_push"},
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
            listed = _load_branch_list()
            if listed.get("success"):
                local_branches = listed.get("local_branches", [])
                remote_branches = listed.get("remote_branches", [])
                current_branch = listed.get("current_branch", "")

                local_lines = [
                    (f"* {name}" if name == current_branch else f"  {name}")
                    for name in local_branches
                ]
                remote_lines = [f"  {name}" for name in remote_branches]
                content = (
                    f"[bold]{t('menu_branch_list_local_title')}[/bold]\n"
                    f"{chr(10).join(local_lines) if local_lines else t('menu_branch_list_empty')}\n\n"
                    f"[bold]{t('menu_branch_list_remote_title')}[/bold]\n"
                    f"{chr(10).join(remote_lines) if remote_lines else t('menu_branch_list_empty')}"
                )
                console.print(
                    Panel(
                        f"[white]{content}[/white]",
                        title=t("menu_branch_list_title"),
                        border_style="cyan",
                    )
                )
            else:
                console.print(f"[red]{listed.get('error', t('menu_branch_generic_error'))}[/red]")
            _pause_menu()
            continue

        if action in {"bulk_delete", "bulk_push"}:
            _run_bulk_action(action)
            continue

        if action == "switch":
            listed = _load_branch_list()
            if not listed.get("success"):
                console.print(f"[red]{listed.get('error', t('menu_branch_generic_error'))}[/red]")
                _pause_menu()
                continue

            current_branch = listed.get("current_branch", "")
            all_branches = listed.get("all_branch_names", [])
            branch_choices = _build_branch_choices(all_branches, current_branch, include_current=True)
            if not branch_choices:
                console.print(f"[yellow]{t('menu_branch_list_empty')}[/yellow]")
                _pause_menu()
                continue

            selected_branch = _inquirer_select(
                t("menu_branch_select_existing_prompt"),
                choices=branch_choices + [{"name": t("menu_action_back"), "value": "back"}],
                default=current_branch if current_branch else None,
                pointer="❯",
                qmark="🌿",
                amark="✓",
                cycle=True,
            )
            if selected_branch == "back":
                continue

            switch_res = run_async(
                kernel.run(
                    "core/git-branch",
                    {"action": "switch", "branch_name": selected_branch, "repo_path": repo_path},
                )
            )
            if switch_res.get("success"):
                console.print(f"[bold green]{t('menu_branch_switch_ok', branch=selected_branch)}[/bold green]")
            else:
                error_text = switch_res.get("message") or switch_res.get("error") or t("menu_branch_generic_error")
                console.print(f"[bold red]{error_text}[/bold red]")
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
