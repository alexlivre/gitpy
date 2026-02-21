import typer
import asyncio
import sys
import os
from typing import Optional

# Fix Windows encoding: force UTF-8 to prevent 'charmap' codec errors with emojis
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

from vibe_core import kernel
from rich.console import Console
from rich.panel import Panel
from rich import box
from dotenv import load_dotenv

# Inicializa a aplicação Typer
app_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(app_dir, ".env"))

app = typer.Typer(
    help="GitPy: Agente de DevOps Autônomo.",
    add_completion=False,
    no_args_is_help=False
)

def run_async(coro):
    """Auxiliar para rodar corrotinas em contexto síncrono do Typer."""
    return asyncio.run(coro)

@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    debug: bool = typer.Option(False, "--debug", help="Exibe logs detalhados de execução."),
    path: str = typer.Option(".", "--path", "-p", help="Caminho do repositório alvo.")
):
    """
    GitPy: Seu Co-Piloto DevOps.
    
    Use 'gitpy auto' para o modo automático.
    """
    # Armazena opções globais no contexto
    ctx.obj = {"debug": debug, "path": path}

    # Se nenhum subcomando foi invocado, exibe a tela de boas-vindas
    if ctx.invoked_subcommand is None:
        console = Console()
        
        console.print(Panel.fit(
            "[bold purple]GitPy[/bold purple] [white]v1.0[/white]\n"
            "[italic]The Vibe-Coded DevOps Agent[/italic]",
            border_style="purple",
            box=box.ROUNDED
        ))

        console.print("\n[bold]Uso:[/bold] [cyan]gitpy auto[/cyan] — Analisa, gera commit e faz push automaticamente.")
        console.print("\n[bold]Flags úteis:[/bold]")
        console.print("  [green]--dry-run[/green]    Simula sem executar")
        console.print("  [green]--no-push[/green]    Commit local, sem push")
        console.print("  [green]-m 'texto'[/green]   Dica de contexto para a IA")
        console.print("  [green]-y[/green]           Confirma tudo automaticamente")
        console.print("  [green]--model X[/green]    Escolhe o provider (groq, openai, gemini, ollama)")
        console.print("\n[dim]Dica: gitpy auto --help para detalhes completos.[/dim]")

@app.command()
def auto(
    ctx: typer.Context,
    wip: bool = typer.Option(False, "--wip", help="Modo Work-In-Progress (ignora verificações de qualidade)."),
    no_push: bool = typer.Option(False, "--no-push", help="Realiza commit local mas não envia ao remoto."),
    message: Optional[str] = typer.Option(None, "--message", "-m", help="Dica de contexto para a IA."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Simula ações sem executar comandos Git."),
    model: str = typer.Option("auto", "--model", help="Provider de IA (auto, openai, gemini, ollama, groq)."),
    yes: bool = typer.Option(False, "--yes", "-y", help="Confirma automaticamente todas as perguntas.")
):
    """
    Modo Autônomo: Analisa mudanças, gera commit e faz push.
    """
    console = Console()
    repo_path = ctx.params.get("path", ".")
    if repo_path == ".":
         repo_path = os.getcwd()
    
    # --- STEALTH MODE START ---
    # 0. Recovery (Tenta restaurar sobras de crash anterior)
    try:
        run_async(kernel.run("tool/tool-stealth", {"action": "restore", "repo_path": repo_path}))
    except Exception:
        pass # Ignora erro no recovery silencioso

    # 0.1 Stash (Esconde arquivos privados)
    # console.print(f"[dim]🙈 Stealth Mode: Checking .gitpy-private...[/dim]")
    stash_res = run_async(kernel.run("tool/tool-stealth", {"action": "stash", "repo_path": repo_path}))
    
    if not stash_res.get("success"):
        console.print(Panel(
            f"[bold red]❌ CRITICAL ERROR: Stealth Stash Failed[/bold red]\n"
            f"{stash_res.get('error')}\n"
            f"[yellow]Aborting to prevent data leak.[/yellow]",
            title="🛡️ Stealth Mode Abort",
            border_style="red"
        ))
        raise typer.Exit(1)
        
    hidden_count = len(stash_res.get("files_moved", []))
    if hidden_count > 0:
        console.print(f"[bold magenta]🥷 Stealth Mode Active: {hidden_count} file(s) hidden.[/bold magenta]")
    # --- STEALTH MODE END ---

    try:
        _auto_impl(ctx, wip, no_push, message, dry_run, model, yes)
    finally:
        # --- STEALTH MODE RESTORE ---
        restore_res = run_async(kernel.run("tool/tool-stealth", {"action": "restore", "repo_path": repo_path}))
        if not restore_res.get("success"):
             console.print(f"[bold red]⚠️  WARNING: Failed to restore private files![/bold red]")
             console.print(f"Details: {restore_res.get('details')}")
        elif restore_res.get("restored_files"):
             console.print(f"[dim]🥷 Stealth Mode: {len(restore_res.get('restored_files'))} file(s) restored.[/dim]")
        # --- STEALTH MODE END ---


def _auto_impl(
    ctx: typer.Context,
    wip: bool = typer.Option(False, "--wip", help="Modo Work-In-Progress (ignora verificações de qualidade)."),
    no_push: bool = typer.Option(False, "--no-push", help="Realiza commit local mas não envia ao remoto."),
    message: Optional[str] = typer.Option(None, "--message", "-m", help="Dica de contexto para a IA."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Simula ações sem executar comandos Git."),
    model: str = typer.Option("auto", "--model", help="Provider de IA (auto, openai, gemini, ollama, groq)."),
    yes: bool = typer.Option(False, "--yes", "-y", help="Confirma automaticamente todas as perguntas.")
):
    """
    Modo Autônomo: Analisa mudanças, gera commit e faz push.
    """
    console = Console()
    
    # Recupera globais do contexto
    repo_path = ctx.obj.get("path", ".")
    debug = ctx.obj.get("debug", False)

    # 0. Auto-Mode (Se chamado via 'auto', já estamos no modo implícito, mas checamos --yes)
    # A lógica original de sys.argv==1 não é mais necessária aqui pois 'auto' é explícito,
    # mas mantemos o suporte a --yes para scripts.

    # Resolve Provider 'auto'
    if model == "auto":
        with console.status("[bold cyan]Detecting AI Provider...", spinner="dots"):
            # Prioridade: Groq > OpenAI > Gemini > Ollama
            detected_provider = "openai" # Fallback default
            
            # Check Groq
            groq_key = run_async(kernel.run("security/sec-keyring", {"action": "get", "service": "groq_api_key"})).get("value")
            if groq_key:
                detected_provider = "groq"
            else:
                # Check OpenAI
                openai_key = run_async(kernel.run("security/sec-keyring", {"action": "get", "service": "openai_api_key"})).get("value")
                if openai_key:
                    detected_provider = "openai"
                else:
                    # Check Gemini
                    gemini_key = run_async(kernel.run("security/sec-keyring", {"action": "get", "service": "gemini_api_key"})).get("value")
                    if gemini_key:
                        detected_provider = "gemini"
        
        model = detected_provider
        console.print(f"[bold cyan]🤖 AI Provider: {model.upper()}[/bold cyan]")

    # 0.5 Smart Ignore Check
    with console.status("[bold green]Checking .gitignore health...", spinner="dots"):
        ignore_res = run_async(kernel.run("tool/tool-ignore", {"action": "scan", "repo_path": repo_path}))
        suggestions = ignore_res.get("suggestions", [])

    if suggestions:
        console.print(Panel(
            f"[yellow]O GitPy detectou arquivos que deveriam ser ignorados:[/yellow]\n"
            f"[bold white]{', '.join(suggestions)}[/bold white]",
            title="🧹 Smart Ignore Suggestion",
            border_style="yellow"
        ))
        if yes or typer.confirm("Deseja adicionar estes padrões ao .gitignore agora?"):
            for pat in suggestions:
                run_async(kernel.run("tool/tool-ignore", {"action": "add", "pattern": pat, "repo_path": repo_path}))
            console.print("[green]✅ .gitignore atualizado! Reiniciando scan...[/green]")

    # 1. Scanner (Rápido)
    with console.status("[bold green]Analysing repository...", spinner="dots"):
        scan_res = run_async(kernel.run("core/git-scanner", {"repo_path": repo_path}))

    if not scan_res.get("is_repo"):
        run_async(kernel.run("cli/cli-renderer", {"action": "error", "message": "Este diretório não é um repositório Git."}))
        raise typer.Exit(1)

    if not scan_res.get("has_changes"):
        console.print("[yellow]✨ Working tree clean. Nada a fazer.[/yellow]")
        return

    # 1.5 Defesa: Muralha de Chumbo (Sanitizer)
    files_changed = scan_res.get("files_changed", [])
    if files_changed:
        sanitizer_res = run_async(kernel.run("security/sec-sanitizer", {"file_paths": files_changed}))
        violations = sanitizer_res.get("violations", 0)
        
        if violations > 0:
            blocked = sanitizer_res.get("blocked_files", [])
            console.print(Panel(
                f"[bold red]🚫 BLOQUEIO DE SEGURANÇA ATIVADO![/bold red]\n\n"
                f"Foram detectados {violations} arquivos proibidos pela Muralha de Chumbo:\n"
                f"{', '.join(blocked)}\n\n"
                f"[yellow]Ação abortada para proteger o repositório.[/yellow]",
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
        console.print("[bold yellow]📦 Vibe Vault Activated: Diff muito grande, usando versão sumarizada.[/bold yellow]")
    else:
        # Modo Direto
        diff_content = diff_data.get("content", "")

    run_async(kernel.run("cli/cli-renderer", {"action": "diff_panel", "data": {"diff": diff_content[:2000]}}))

    # 2. Confirmação do Usuário
    if not yes and not typer.confirm("Gostaria de gerar uma mensagem de commit para estas alterações?"):
        typer.echo("Operação cancelada.")
        raise typer.Exit()

    # 2.5 Leitura do .gitpy (REMOVIDO - Deprecated)
    # gitpy_instructions = ""

    # 3. Brain (Pensando...)
    with console.status(f"[bold purple]GitPy Brain ({model}) is thinking...", spinner="bouncingBall"):
        brain_res = run_async(kernel.run("ai/ai-brain", {
            "diff": diff_content,
            "repo_path": repo_path,
            "hint": message,
            "provider": model,
            "is_truncated": (diff_mode == "ref")
        }))

    if not brain_res.get("success"):
        run_async(kernel.run("cli/cli-renderer", {"action": "error", "message": f"Erro na IA: {brain_res.get('message')}"}))
        raise typer.Exit(1)

    commit_msg = brain_res.get("commit_message")
    
    # Exibe resultado da IA
    console.print(Panel(f"[bold white]{commit_msg}[/bold white]", title="🤖 Generated Commit Message", border_style="purple"))

    # 4. Execução (Commit)
    if dry_run:
        console.print("[cyan][DRY-RUN] Commit seria executado agora.[/cyan]")
        return

    if yes or typer.confirm("Confirmar execução do commit?"):
        with console.status("[bold blue]Committing & Pushing...", spinner="line"):
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
                console.print("[green]Commit realizado com sucesso! ✅[/green]")
                
                # 3. Push
                if not no_push:
                    console.print("[bold blue]Pushing to remote... 🚀[/bold blue]")
                    push_res = run_async(kernel.run("core/git-executor", {
                        "repo_path": repo_path,
                        "command": "push"
                    }))
                    if push_res.get("success"):
                         run_async(kernel.run("cli/cli-renderer", {"action": "success", "message": "Push realizado com sucesso! 🌐"}))
                    else:
                         # Tenta Curar (Git Healer)
                         console.print("[bold red]❌ Falha no push. Acionando Git Healer...[/bold red]")
                         heal_res = run_async(kernel.run("core/git-healer", {
                             "repo_path": repo_path,
                             "failed_command": "git push",
                             "error_output": push_res.get("stderr"),
                             "provider": model,
                             "max_retries": 10
                         }))
                         
                         if heal_res.get("success"):
                             run_async(kernel.run("cli/cli-renderer", {"action": "success", "message": f"Git Healer salvou o dia! 🚑\n{heal_res.get('message')}"}))
                         else:
                             run_async(kernel.run("cli/cli-renderer", {"action": "error", "message": f"Git Healer falhou: {heal_res.get('message')}"}))
            else:
                run_async(kernel.run("cli/cli-renderer", {"action": "error", "message": f"Falha no commit: {exec_res.get('stderr')}"}))
    else:
        console.print("[yellow]Commit cancelado.[/yellow]")


if __name__ == "__main__":
    app()
