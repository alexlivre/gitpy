"""
Central module for GitPy Launcher functionality.
"""
import asyncio
import os
import sys
from typing import Optional

import typer

# Fix Windows encoding: force UTF-8 to prevent 'charmap' codec errors with emojis
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

from dotenv import load_dotenv

# Carrega configurações do servidor/ambiente IMEDIATAMENTE (essencial para i18n)
app_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(app_dir, ".env"))

from rich import box
from rich.console import Console
from rich.panel import Panel

from vibe_core import kernel
from i18n import t

# Inicializa a aplicação Typer
app = typer.Typer(
    help=t("app_help"),
    add_completion=False,
    no_args_is_help=False
)


def run_async(coro):
    """Auxiliar para rodar corrotinas em contexto síncrono do Typer."""
    return asyncio.run(coro)


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    debug: bool = typer.Option(
        False, "--debug", help=t("option_debug_help")),
    path: str = typer.Option(
        ".", "--path", "-p", help=t("option_path_help"))
):
    """
    {t('app_description')}

    {t('app_auto_usage')}
    """
    # Armazena opções globais no contexto
    ctx.obj = {"debug": debug, "path": path}

    # Se nenhum subcomando foi invocado, exibe a tela de boas-vindas
    if ctx.invoked_subcommand is None:
        console = Console()

        console.print(Panel.fit(
            "[bold purple]GitPy[/bold purple] [white]v1.0[/white]\n"
            f"[italic]{t('welcome_subtitle')}[/italic]",
            border_style="purple",
            box=box.ROUNDED
        ))

        console.print(f"\n[bold]{t('usage_auto')}[/bold]")
        console.print(f"\n[bold]{t('useful_flags')}[/bold]")
        console.print(f"  [green]--debug[/green]      [bold magenta]Deep Trace Mode:[/bold magenta] {t('option_debug_help')}")
        console.print(f"  [green]--dry-run[/green]    {t('flag_dry_run')}")
        console.print(f"  [green]--no-push[/green]    {t('flag_no_push')}")
        console.print(f"  [green]-m 'texto'[/green]   {t('flag_message')}")
        console.print(f"  [green]-y[/green]           {t('flag_yes')}")
        console.print(f"  [green]--model X[/green]    {t('flag_model')}")
        console.print(f"\n[dim]{t('help_hint')}[/dim]")


@app.command(help=t("cmd_auto_help"))
def auto(
    ctx: typer.Context,
    wip: bool = typer.Option(
        False, "--wip", help=t("option_wip_help")),
    no_push: bool = typer.Option(
        False, "--no-push", help=t("flag_no_push")),
    nobuild: bool = typer.Option(
        False, "--nobuild", help=t("option_nobuild_help")),
    message: Optional[str] = typer.Option(
        None, "--message", "-m", help=t("flag_message")),
    dry_run: bool = typer.Option(
        False, "--dry-run", help=t("flag_dry_run")),
    model: str = typer.Option(os.getenv("AI_PROVIDER", "auto"), "--model",
                              help=t("flag_model")),
    debug: bool = typer.Option(
        False, "--debug", help=t("option_debug_help")),
    yes: bool = typer.Option(
        False, "--yes", "-y", help=t("flag_yes")),
    branch: Optional[str] = typer.Option(
        None, "--branch", "-b", help=t("option_branch_help"))
):
    """
    Modo Autônomo: Analisa mudanças, gera commit e faz push.
    """
    console = Console()
    repo_path = ctx.params.get("path", ".")
    if repo_path == ".":
        repo_path = os.getcwd()

    # --- BRANCH MANAGEMENT START ---
    original_branch = None
    if branch:
        # Armazenar branch atual
        try:
            current_res = run_async(kernel.run("core/git-branch", 
                {"action": "current", "repo_path": repo_path}))
            if current_res.get("success"):
                original_branch = current_res.get("current_branch")
        except Exception:
            pass  # Ignora erro ao obter branch atual
        
        # Validar nome da branch
        validation_res = run_async(kernel.run("core/git-branch", 
            {"action": "validate", "branch_name": branch, "repo_path": repo_path}))
        if not validation_res.get("valid"):
            console.print(Panel(
                f"[bold red]{t('branch_invalid_name', branch=branch)}[/bold red]\n"
                f"{validation_res.get('error')}",
                title="❌ Erro de Validação",
                border_style="red"
            ))
            raise typer.Exit(1)
        
        # Verificar se branch existe e criar/alternar conforme necessário
        exists_res = run_async(kernel.run("core/git-branch", 
            {"action": "exists", "branch_name": branch, "repo_path": repo_path}))
        
        if exists_res.get("exists"):
            console.print(f"[bold yellow]{t('branch_exists', branch=branch)}[/bold yellow]")
            action_msg = t("branch_switching", branch=branch)
        else:
            action_msg = t("branch_creating", branch=branch)
        
        with console.status(f"[bold cyan]{action_msg}[/bold cyan]", spinner="dots"):
            if exists_res.get("exists"):
                # Alternar para branch existente
                switch_res = run_async(kernel.run("core/git-branch", 
                    {"action": "switch", "branch_name": branch, "repo_path": repo_path}))
            else:
                # Criar e alternar para nova branch
                # Primeiro cria, depois alterna
                create_res = run_async(kernel.run("core/git-branch", 
                    {"action": "create", "branch_name": branch, "repo_path": repo_path}))
                if create_res.get("success"):
                    switch_res = run_async(kernel.run("core/git-branch", 
                        {"action": "switch", "branch_name": branch, "repo_path": repo_path}))
                else:
                    switch_res = {"success": False, "error": create_res.get("error")}
        
        if not switch_res.get("success"):
            console.print(Panel(
                f"[bold red]{t('branch_error', branch=branch, error=switch_res.get('error'))}[/bold red]",
                title="❌ Erro na Branch",
                border_style="red"
            ))
            raise typer.Exit(1)
        
        console.print(f"[bold green]{t('branch_success', branch=branch)}[/bold green]")
    # --- BRANCH MANAGEMENT END ---

    # --- STEALTH MODE START ---
    # 0. Recovery (Tenta restaurar sobras de crash anterior)
    try:
        run_async(kernel.run("tool/tool-stealth",
                  {"action": "restore", "repo_path": repo_path}))
    except Exception:
        pass  # Ignora erro no recovery silencioso

    # 0.1 Stash (Esconde arquivos privados)
    # console.print(f"[dim]🙈 Stealth Mode: Checking .gitpy-private...[/dim]")
    stash_res = run_async(kernel.run("tool/tool-stealth",
                          {"action": "stash", "repo_path": repo_path}))

    if not stash_res.get("success"):
        console.print(Panel(
            f"[bold red]{t('stealth_stash_failed')}[/bold red]\n"
            f"{stash_res.get('error')}\n"
            f"[yellow]{t('stealth_abort_prevent_leak')}[/yellow]",
            title="🛡️ Stealth Mode Abort",
            border_style="red"
        ))
        raise typer.Exit(1)

    hidden_count = len(stash_res.get("files_moved", []))
    if hidden_count > 0:
        console.print(
            f"[bold magenta]{t('stealth_active', count=hidden_count)}[/bold magenta]")
    # --- STEALTH MODE END ---

    try:
        _auto_impl(ctx, wip, no_push, nobuild,
                   message, dry_run, model, debug, yes, branch)
    finally:
        # --- STEALTH MODE RESTORE ---
        restore_res = run_async(kernel.run(
            "tool/tool-stealth", {"action": "restore", "repo_path": repo_path}))
        if not restore_res.get("success"):
            console.print(
                f"[bold red]{t('stealth_restore_warn')}[/bold red]")
            console.print(f"Details: {restore_res.get('details')}")
        elif restore_res.get("restored_files"):
            console.print(
                f"[dim]{t('stealth_restored', count=len(restore_res.get('restored_files')))}[/dim]")
        # --- STEALTH MODE END ---


def _auto_impl(
    ctx: typer.Context,
    wip: bool = typer.Option(
        False, "--wip", help="Modo Work-In-Progress (ignora verificações de qualidade)."),
    no_push: bool = typer.Option(
        False, "--no-push", help="Realiza commit local mas não envia ao remoto."),
    nobuild: bool = typer.Option(
        False, "--nobuild", help="Adiciona [CI Skip] à mensagem de commit para evitar deploy automático."),
    message: Optional[str] = typer.Option(
        None, "--message", "-m", help="Dica de contexto para a IA."),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Simula ações sem executar comandos Git."),
    model: str = typer.Option(os.getenv("AI_PROVIDER", "auto"), "--model",
                              help="Provider de IA (auto, openrouter, openai, gemini, ollama, groq)."),
    debug: bool = typer.Option(
        False, "--debug", help="Deep Trace: Ativa log profundo em .vibe-debug.log."),
    yes: bool = typer.Option(
        False, "--yes", "-y", help="Confirma automaticamente todas as perguntas."),
    branch: Optional[str] = typer.Option(
        None, "--branch", "-b", help="Criar/usar branch de teste para operações.")
):
    """
    Modo Autônomo: Analisa mudanças, gera commit e faz push.
    """
    console = Console()

    # Recupera globais do contexto ou da chamada direta do auto
    repo_path = ctx.obj.get("path", ".")
    global_debug = ctx.obj.get("debug", False)

    # Prevalesce a flag --debug se ela vier localmente no subcomando
    kernel_debug = debug or global_debug

    # Pluga o modo debug no kernel (novo rastreador deep trace)
    kernel.debug_mode = kernel_debug

    # 0. Auto-Mode (Se chamado via 'auto', já estamos no modo implícito, mas checamos --yes)
    # A lógica original de sys.argv==1 não é mais necessária aqui pois 'auto' é explícito,
    # mas mantemos o suporte a --yes para scripts.

    # Resolve Provider 'auto'
    if model == "auto":
        with console.status(f"[bold cyan]{t('detecting_ai')}", spinner="dots"):
            # Prioridade: OpenRouter > Groq > OpenAI > Gemini > Ollama
            detected_provider = "openai"  # Fallback default
            # ... (logica de detecção omitida para brevidade no replace se possivel, mas mantida aqui)
            
            # Re-implementando a detecção por seguranca no chunk
            openrouter_key = run_async(kernel.run(
                "security/sec-keyring", {"action": "get", "service": "openrouter_api_key"})).get("value")
            if openrouter_key:
                detected_provider = "openrouter"
            else:
                groq_key = run_async(kernel.run(
                    "security/sec-keyring", {"action": "get", "service": "groq_api_key"})).get("value")
                if groq_key:
                    detected_provider = "groq"
                else:
                    openai_key = run_async(kernel.run(
                        "security/sec-keyring", {"action": "get", "service": "openai_api_key"})).get("value")
                    if openai_key:
                        detected_provider = "openai"
                    else:
                        gemini_key = run_async(kernel.run(
                            "security/sec-keyring", {"action": "get", "service": "gemini_api_key"})).get("value")
                        if gemini_key:
                            detected_provider = "gemini"

        model = detected_provider
        console.print(f"[bold cyan]{t('ai_provider_label', model=model.upper())}[/bold cyan]")

    # 0.5 Smart Ignore Check
    with console.status(f"[bold green]{t('checking_ignore')}", spinner="dots"):
        ignore_res = run_async(kernel.run(
            "tool/tool-ignore", {"action": "scan", "repo_path": repo_path}))
        suggestions = ignore_res.get("suggestions", [])

    if suggestions:
        console.print(Panel(
            f"[yellow]{t('ignore_detected_files')}[/yellow]\n"
            f"[bold white]{', '.join(suggestions)}[/bold white]",
            title=t("ignore_suggestion_title"),
            border_style="yellow"
        ))
        if yes or typer.confirm(t("ignore_confirm")):
            for pat in suggestions:
                run_async(kernel.run(
                    "tool/tool-ignore", {"action": "add", "pattern": pat, "repo_path": repo_path}))
            console.print(
                f"[green]{t('ignore_updated_restart')}[/green]")

    # 1. Scanner (Rápido)
    with console.status(f"[bold green]{t('analyzing_repo')}", spinner="dots"):
        scan_res = run_async(kernel.run(
            "core/git-scanner", {"repo_path": repo_path}))

    if not scan_res.get("is_repo"):
        run_async(kernel.run("cli/cli-renderer",
                  {"action": "error", "message": t("error_not_repo")}))
        raise typer.Exit(1)

    if not scan_res.get("has_changes"):
        console.print(f"[yellow]{t('clean_tree')}[/yellow]")
        return

    # 1.5 Defesa: Muralha de Chumbo (Sanitizer)
    files_changed = scan_res.get("files_changed", [])
    if files_changed:
        sanitizer_res = run_async(kernel.run(
            "security/sec-sanitizer", {"file_paths": files_changed}))
        violations = sanitizer_res.get("violations", 0)

        if violations > 0:
            blocked = sanitizer_res.get("blocked_files", [])
            console.print(Panel(
                f"[bold red]{t('security_block_activated')}[/bold red]\n\n"
                f"{t('security_files_detected', count=violations)}\n"
                f"{', '.join(blocked)}\n\n"
                f"[yellow]{t('security_action_blocked')}[/yellow]",
                title="🛡️ Security Blocklist",
                border_style="red"
            ))
            # Falha silenciosa para não quebrar pipelines de CI, mas com exit code 1
            raise typer.Exit(1)

    # Mostra Diff Resumido
    diff_data = scan_res.get("diff_data", {})
    diff_mode = diff_data.get("mode", "none")

    if diff_mode == "ref":
        # Modo Vibe Vault (Diff Grande)
        diff_content = diff_data.get("preview", "")
        console.print(
            f"[bold yellow]{t('vibe_vault_activated')}[/bold yellow]")
    else:
        # Modo Direto
        diff_content = diff_data.get("content", "")

    run_async(kernel.run("cli/cli-renderer",
              {"action": "diff_panel", "data": {"diff": diff_content[:2000]}}))

    # 2. Confirmação do Usuário
    if not yes and not typer.confirm(t("confirm_gen_commit")):
        typer.echo(t("op_cancelled"))
        raise typer.Exit()

    # 2.5 Leitura do .gitpy (REMOVIDO - Deprecated)
    # gitpy_instructions = ""

    # 3. Brain (Pensando...)
    with console.status(f"[bold purple]{t('brain_thinking', model=model)}", spinner="bouncingBall"):
        # Captura o idioma do commit do .env (com sanitização simples via split('#'))
        raw_commit_lang = os.getenv("COMMIT_LANGUAGE", "en")
        commit_lang = raw_commit_lang.split('#')[0].strip().lower()

        brain_res = run_async(kernel.run("ai/ai-brain", {
            "diff": diff_content,
            "repo_path": repo_path,
            "hint": message,
            "provider": model,
            "commit_lang": commit_lang,
            "is_truncated": (diff_mode == "ref")
        }))

    if not brain_res.get("success"):
        run_async(kernel.run("cli/cli-renderer",
                  {"action": "error", "message": t("error_ai", message=brain_res.get('message'))}))
        raise typer.Exit(1)

    commit_msg = brain_res.get("commit_message")

    # Adiciona [CI Skip] se --nobuild estiver ativo
    if nobuild:
        commit_msg = f"[CI Skip] {commit_msg}"

    # Exibe resultado da IA
    console.print(Panel(f"[bold white]{commit_msg}[/bold white]",
                  title=t("generated_commit_title"), border_style="purple"))

    # 4. Execução (Commit)
    if dry_run:
        console.print(f"[cyan]{t('dry_run_commit')}[/cyan]")
        return

    if yes or typer.confirm(t("confirm_exec_commit")):
        with console.status(f"[bold blue]{t('committing_pushing')}", spinner="line"):
            # 1. Staging (git add -A)
            run_async(kernel.run("core/git-executor", {
                "repo_path": repo_path,
                "command": "add -A"
            }))

            # 1.2 Smart Removal (REMOVIDO - Deprecated)
            # removed_files = brain_res.get("removed_files", [])

            # 1.5 Smart Exclusion (REMOVIDO - Deprecated)
            # excluded_files = brain_res.get("excluded_files", [])

            # 1.6 Verificação de Stage
            # Como removemos a lógica de exclusão, assumimos que o stage continua válido se o diff tinha algo.

            # 2. Commit
            # Usar subprocess com lista de argumentos evita problemas de shell com aspas
            # O git-executor usa shlex.split no comando string, o que pode falhar com aspas aninhadas
            # Melhor abordagem: Remover aspas simples e duplas externas da mensagem para evitar quebra do shlex

            # Sanitização simples da mensagem para o comando CLI
            safe_msg = commit_msg.replace("'", '"')

            exec_res = run_async(kernel.run("core/git-executor", {
                "repo_path": repo_path,
                "command": f"commit -m '{safe_msg}'"
            }))

            if exec_res.get("success"):
                console.print(f"[green]{t('commit_success')}[/green]")

                # 3. Push
                if not no_push:
                    console.print(
                        f"[bold blue]{t('pushing_remote')}[/bold blue]")
                    push_res = run_async(kernel.run("core/git-executor", {
                        "repo_path": repo_path,
                        "command": "push"
                    }))
                    if push_res.get("success"):
                        run_async(kernel.run(
                            "cli/cli-renderer", {"action": "success", "message": t("push_success")}))
                    else:
                        # Tenta Curar (Git Healer)
                        console.print(
                            f"[bold red]{t('push_failed_healer')}[/bold red]")
                        heal_res = run_async(kernel.run("core/git-healer", {
                            "repo_path": repo_path,
                            "failed_command": "git push",
                            "error_output": push_res.get("stderr"),
                            "provider": model,
                            "max_retries": 10
                        }))

                        if heal_res.get("success"):
                            run_async(kernel.run(
                                "cli/cli-renderer", {"action": "success", "message": t("healer_saved_day", message=heal_res.get('message'))}))
                        else:
                            run_async(kernel.run(
                                "cli/cli-renderer", {"action": "error", "message": t("healer_failed", message=heal_res.get('message'))}))
            else:
                run_async(kernel.run(
                    "cli/cli-renderer", {"action": "error", "message": t("commit_failed", error=exec_res.get('stderr'))}))
    else:
        console.print(f"[yellow]{t('op_cancelled')}[/yellow]")


@app.command()
def check_ai(
    ctx: typer.Context
):
    """
    Diagnóstico de IA: Testa a conectividade e configuração de todos os provedores.
    """
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
            # 1. Check Config (Key)
            key_res = await kernel.run("security/sec-keyring", {"action": "get", "service": f"{p}_api_key"})
            has_key = key_res.get("success", False)
            
            if not has_key and p != "ollama":
                results.append((p.upper(), "🟡", "-", t("error_no_key")))
                continue
            
            if p == "ollama":
                config_status = t("config_local")
            else:
                config_status = t("config_ok")

            # 2. Test Connection (Ping)
            test_prompt = "Responda apenas 'PONG'."
            try:
                # Usamos um timeout menor para o check
                test_res = await kernel.run(f"ai/ai-{p}", {
                    "prompt": test_prompt,
                    "system_instruction": "Você é um testador. Responda apenas PONG.",
                    "max_tokens": 10
                }, timeout=15)
                
                if test_res.get("error"):
                    status = "🔴"
                    details = test_res.get("message", "Erro desconhecido")
                else:
                    status = "🟢"
                    details = t("status_pinging", model=test_res.get('model_used', 'default'))
            except Exception as e:
                status = "🔴"
                details = str(e)

            results.append((p.upper(), config_status, status, details))
        return results

    with console.status(f"[bold purple]{t('running_diag')}", spinner="earth"):
        diag_results = run_async(run_diagnostics())
        for row in diag_results:
            table.add_row(*row)

    console.print(table)
    console.print(f"\n[dim]{t('diag_hint')}[/dim]")


if __name__ == "__main__":
    app()
