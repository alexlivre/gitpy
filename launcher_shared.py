"""
Funções compartilhadas entre os módulos do launcher.
Evita importação circular entre launcher.py e seus submódulos.
"""
import asyncio
import os
from dataclasses import dataclass
from typing import Optional

import typer


# Diretório da aplicação (usado por launcher_reset.py)
app_dir = os.path.dirname(os.path.abspath(__file__))


@dataclass
class AutoOptions:
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


def run_async(coro):
    """Auxiliar para rodar corrotinas em contexto sincrono do Typer."""
    return asyncio.run(coro)


def _resolve_repo_path(ctx: typer.Context) -> str:
    """Resolve o caminho do repositório a partir do contexto."""
    repo_path = "."
    if ctx.obj and "path" in ctx.obj:
        repo_path = ctx.obj.get("path", ".")
    elif "path" in ctx.params:
        repo_path = ctx.params.get("path", ".")

    if repo_path == ".":
        return os.getcwd()
    return repo_path
