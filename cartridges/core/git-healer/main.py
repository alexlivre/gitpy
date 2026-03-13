"""
Central module for git-healer functionality.
"""
from typing import Any, Dict

from vibe_core import kernel


async def process(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Git Healer: Médico do Repositório.
    Tenta corrigir erros de execução do Git usando IA.
    """
    repo_path = payload.get("repo_path")
    failed_command = payload.get("failed_command")
    error_output = payload.get("error_output")
    provider = payload.get("provider", "openai")
    max_retries = payload.get("max_retries", 10)

    if not repo_path or not error_output:
        return {"success": False, "error": "MISSING_ARGS", "message": "repo_path e error_output são obrigatórios."}

    print(
        f"[bold yellow]🚑 Git Healer acionado! Tentando corrigir erro no comando '{failed_command}'...[/bold yellow]")

    history = []
    current_error = error_output

    for attempt in range(1, max_retries + 1):
        print(
            f"[bold cyan]🔄 Tentativa de Cura {attempt}/{max_retries}...[/bold cyan]")

        # 1. Diagnóstico e Prescrição (IA)
        system_prompt = """Você é um Especialista em Git e Resolução de Conflitos.
        Seu objetivo é analisar um erro de execução do Git e fornecer APENAS a sequência de comandos para corrigi-lo.
        
        Regras:
        - Responda APENAS com os comandos, um por linha.
        - Não use blocos de código (```), não use explicações.
        - Se o erro for de 'non-fast-forward', sugira 'git pull --rebase'.
        - IMPORTANTE: Se um comando da sua lista falhar (ex: conflito no pull), a execução PARA e eu volto para você com o erro.
        - Se o erro atual for um CONFLITO (merge/rebase em andamento), NÃO SUGIRA 'git rebase --abort' a menos que queira desistir.
        - Para resolver conflitos: Sugira apenas 'git add .' e 'git rebase --continue' (ou commit). O estado do repositório é preservado entre tentativas.
        """

        user_prompt = f"""
        Comando que falhou: {failed_command}
        Erro original:
        {current_error}
        
        Histórico de tentativas anteriores:
        {history}
        
        Quais comandos devo executar para corrigir isso e permitir que '{failed_command}' funcione?
        """

        # Chama a IA
        try:
            adapter_name = f"ai/ai-{provider}"
            if provider == "auto":
                # Healer precisa de um provider concreto. Se veio 'auto', o launcher.py já deveria ter resolvido,
                # mas por segurança, tentamos descobrir ou fallback para openai.
                # (Simplificação: assume que quem chamou passou o resolved provider, ou usa openai)
                adapter_name = "ai/ai-openai"

            llm_res = await kernel.run(adapter_name, {
                "prompt": user_prompt,
                "system_instruction": system_prompt
            })

            prescription = llm_res.get("text", "").strip()
            # Limpa formatação Markdown se a IA desobedecer
            prescription = prescription.replace(
                "```bash", "").replace("```", "").strip()

            commands = [cmd.strip()
                        for cmd in prescription.split('\n') if cmd.strip()]

        except Exception as e:
            print(f"[red]❌ Erro na consulta ao médico (IA): {e}[/red]")
            return {"success": False, "message": f"IA falhou: {e}"}

        if not commands:
            print("[yellow]⚠️ IA não sugeriu correções.[/yellow]")
            break

        print(f"[dim]💊 Prescrição:[/dim] {commands}")

        # 2. Execução da Cirurgia (Execução de Comandos)
        batch_success = True
        last_cmd_output = ""

        for cmd in commands:
            # Remove 'git ' do início se houver, pois git-executor adiciona
            cmd_clean = cmd
            if cmd.startswith("git "):
                cmd_clean = cmd[4:]

            exec_res = await kernel.run("core/git-executor", {
                "repo_path": repo_path,
                "command": cmd_clean
            })

            if not exec_res.get("success"):
                batch_success = False
                current_error = exec_res.get("stderr")
                print(
                    f"[red]❌ Falha na cura ao executar '{cmd}': {current_error}[/red]")
                break
            else:
                print(f"[green]✅ '{cmd}' executado com sucesso.[/green]")

        history.append({"attempt": attempt, "commands": commands,
                       "success": batch_success, "error": current_error})

        if batch_success:
            # Se a cura funcionou (todos os comandos de correção rodaram),
            # tentamos rodar o comando ORIGINAL que havia falhado.
            print(
                f"[bold green]✨ Cura aplicada! Re-tentando comando original: '{failed_command}'...[/bold green]")

            cmd_orig_clean = failed_command
            if failed_command.startswith("git "):
                cmd_orig_clean = failed_command[4:]

            retry_orig = await kernel.run("core/git-executor", {
                "repo_path": repo_path,
                "command": cmd_orig_clean
            })

            if retry_orig.get("success"):
                return {"success": True, "message": "Repositório curado e comando original executado com sucesso!", "attempts": attempt}
            else:
                current_error = retry_orig.get("stderr")
                print(
                    f"[red]🤕 O comando original ainda falha. Tentando nova estratégia...[/red]")
                # Loop continua para próxima tentativa

    return {
        "success": False,
        "message": f"Não foi possível curar o repositório após {max_retries} tentativas.",
        "last_error": current_error
    }
