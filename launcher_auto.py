"""
Auto mode do GitPy - Commit automático com IA.
"""
import os
import sys

import typer
from rich.console import Console
from rich.panel import Panel

from vibe_core import VibeVault, kernel
from i18n import t
from launcher_shared import run_async, _resolve_repo_path, AutoOptions
from env_config import COMMIT_LANGUAGE
from typing import Callable


def _run_auto_with_guards(
    ctx: typer.Context,
    options: AutoOptions,
    confirm_fn: Callable[[str], bool],
) -> None:
    console = Console()
    repo_path = _resolve_repo_path(ctx)
    global_debug = (ctx.obj or {}).get("debug", False)
    kernel.debug_mode = options.debug or global_debug

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
        diff_content = ""
        diff_ref = diff_data.get("data_ref")
        if diff_ref:
            recovered_diff = VibeVault.retrieve(diff_ref)
            if isinstance(recovered_diff, str) and recovered_diff.strip():
                diff_content = recovered_diff

        if not diff_content:
            diff_content = diff_data.get("preview", "")
            console.print(f"[bold yellow]{t('vibe_vault_activated')}[/bold yellow]")
        else:
            console.print(f"[bold yellow]{t('vibe_vault_activated')}[/bold yellow] [green](full diff loaded)[/green]")
    else:
        diff_content = diff_data.get("content", "")

    run_async(kernel.run("cli/cli-renderer", {"action": "diff_panel", "data": {"diff": diff_content[:2000]}}))

    with console.status(f"[bold purple]{t('brain_thinking', model=model)}", spinner="bouncingBall"):
        # Usa o idioma de commit já carregado do env_config
        commit_lang = COMMIT_LANGUAGE

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

    # Loop para permitir regenerar a mensagem de commit
    while True:
        if options.yes:
            # Com --yes, executa diretamente sem perguntar
            action = "execute"
        else:
            # Pergunta ao usuário o que fazer
            try:
                from launcher_menu import _inquirer_select
                action = _inquirer_select(
                    t("commit_options"),
                    choices=[
                        {"name": t("option_execute"), "value": "execute"},
                        {"name": t("option_regenerate"), "value": "regenerate"},
                        {"name": t("option_cancel"), "value": "cancel"},
                    ]
                )
            except ImportError:
                # Se não tiver InquirerPy, usa confirmação simples
                if confirm_fn(t("confirm_exec_commit")):
                    action = "execute"
                else:
                    action = "cancel"

        if action == "execute":
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
            break  # Sai do loop após executar

        elif action == "regenerate":
            # Regenera a mensagem de commit
            with console.status(f"[bold purple]{t('brain_thinking', model=model)}", spinner="bouncingBall"):
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
            # Continua no loop para perguntar novamente

        else:  # cancel
            console.print(f"[yellow]{t('op_cancelled')}[/yellow]")
            break


def _run_auto_with_branch_guards(
    ctx: typer.Context,
    options: AutoOptions,
    confirm_fn: Callable[[str], bool],
) -> None:
    """Wrapper que adiciona guards de branch antes de rodar auto."""
    console = Console()
    repo_path = _resolve_repo_path(ctx)

    def _is_tty() -> bool:
        try:
            return sys.stdin.isatty() and sys.stdout.isatty()
        except Exception:
            return False

    if not options.branch and _is_tty():
        try:
            from launcher_menu import _inquirer_select

            # Obter branch atual para exibir no menu
            current_branch = "main"  # valor padrão
            try:
                listed = run_async(
                    kernel.run("core/git-branch", {"action": "list", "repo_path": repo_path})
                )
                if listed.get("success"):
                    current_branch = listed.get("current_branch", "main")
            except Exception:
                pass
            
            branch_mode = _inquirer_select(
                t("menu_prompt_branch_mode"),
                choices=[
                    {"name": t("menu_prompt_branch_none").format(branch=current_branch), "value": "none"},
                    {"name": t("menu_prompt_branch_existing"), "value": "existing"},
                    {"name": t("menu_action_back"), "value": "none"},
                ],
                default="none",
                pointer="❯",
                qmark="🌿",
                amark="✓",
                cycle=True,
            )

            if branch_mode == "existing":
                listed = run_async(
                    kernel.run("core/git-branch", {"action": "list", "repo_path": repo_path})
                )
                if listed.get("success"):
                    current_branch = listed.get("current_branch", "")
                    branches = listed.get("all_branch_names", [])
                    if branches:
                        choices = []
                        for name in branches:
                            label = f"{name} [dim]({t('menu_branch_current_marker')})[/dim]" if name == current_branch else name
                            choices.append({"name": label, "value": name})

                        selected_branch = _inquirer_select(
                            t("menu_branch_select_existing_prompt"),
                            choices=choices + [{"name": t("menu_action_back"), "value": "back"}],
                            default=current_branch if current_branch else None,
                            pointer="❯",
                            qmark="🌿",
                            amark="✓",
                            cycle=True,
                        )
                        if selected_branch != "back":
                            options.branch = selected_branch
        except Exception:
            pass

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
        _run_auto_with_guards(ctx, options, confirm_fn=confirm_fn)
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
