"""
Diagnósticos de IA do GitPy.
"""
from rich.console import Console
from rich.table import Table
from rich import box

from vibe_core import kernel
from i18n import t
from launcher_shared import run_async


def _run_check_ai_diagnostics() -> None:
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


def _show_gitpy_resources() -> None:
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
