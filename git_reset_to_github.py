#!/usr/bin/env python3
"""
Script para resetar completamente um repositório Git local para a versão do GitHub.
Autor: Gita - Assistente de Git/GitHub
Data: 2024
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Optional, Tuple


class GitResetAutomator:
    """Classe principal para automação do reset Git."""

    def __init__(self, verbose: bool = True, force: bool = True):
        """
        Inicializa o automator.

        Args:
            verbose: Exibe informações detalhadas durante a execução
            force: Não pergunta confirmações, executa automaticamente
        """
        self.verbose = verbose
        self.force = force
        self.current_dir = Path.cwd()
        self.git_dir = None
        self.original_branch = None
        self.remote_branch = None

    def log(self, message: str, level: str = "INFO") -> None:
        """Log de mensagens formatadas."""
        if self.verbose:
            timestamp = time.strftime("%H:%M:%S")
            print(f"[{timestamp}] [{level}] {message}")

    def run_command(self, command: List[str], capture_output: bool = True) -> Tuple[int, str, str]:
        """
        Executa um comando no shell.

        Returns:
            Tuple: (return_code, stdout, stderr)
        """
        try:
            self.log(f"Executando: {' '.join(command)}", "CMD")
            result = subprocess.run(
                command,
                capture_output=capture_output,
                text=True,
                encoding='utf-8',
                errors='ignore'
            )

            if capture_output:
                if result.stdout and self.verbose:
                    self.log(f"Saída: {result.stdout.strip()[:200]}", "OUT")
                if result.stderr and result.returncode != 0:
                    self.log(f"Erro: {result.stderr.strip()[:200]}", "ERR")

            return result.returncode, result.stdout, result.stderr

        except FileNotFoundError:
            self.log(f"Comando não encontrado: {command[0]}", "ERROR")
            return 1, "", f"Comando {command[0]} não encontrado"
        except Exception as e:
            self.log(f"Erro ao executar comando: {str(e)}", "ERROR")
            return 1, "", str(e)

    def check_git_installed(self) -> bool:
        """Verifica se o Git está instalado no sistema."""
        self.log("Verificando se Git está instalado...")
        return_code, stdout, stderr = self.run_command(["git", "--version"])

        if return_code == 0:
            self.log("✓ Git está instalado")
            return True
        else:
            self.log("✗ Git não está instalado ou não está no PATH", "ERROR")
            return False

    def check_git_repository(self) -> bool:
        """Verifica se o diretório atual é um repositório Git."""
        self.log(f"Verificando se {self.current_dir} é um repositório Git...")

        # Primeiro, verifica se há um diretório .git
        git_path = self.current_dir / ".git"
        if git_path.exists():
            self.git_dir = git_path
            self.log(f"✓ Diretório .git encontrado em {git_path}")
            return True

        # Tenta usar git rev-parse para verificar
        return_code, stdout, stderr = self.run_command(
            ["git", "rev-parse", "--git-dir"])

        if return_code == 0:
            self.git_dir = Path(stdout.strip())
            self.log(f"✓ Repositório Git encontrado: {self.git_dir}")
            return True
        else:
            self.log("✗ Diretório atual não é um repositório Git", "ERROR")
            return False

    def get_current_branch(self) -> Optional[str]:
        """Obtém o nome da branch atual."""
        self.log("Obtendo branch atual...")
        return_code, stdout, stderr = self.run_command(
            ["git", "branch", "--show-current"])

        if return_code == 0 and stdout.strip():
            self.original_branch = stdout.strip()
            self.log(f"✓ Branch atual: {self.original_branch}")
            return self.original_branch
        else:
            # Tenta método alternativo
            return_code, stdout, stderr = self.run_command(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"])
            if return_code == 0 and stdout.strip():
                self.original_branch = stdout.strip()
                self.log(f"✓ Branch atual: {self.original_branch}")
                return self.original_branch

        self.log("✗ Não foi possível determinar a branch atual", "ERROR")
        return None

    def get_all_branches(self) -> Tuple[List[str], List[str]]:
        """Obtém todas as branches locais e remotas."""
        self.log("Listando todas as branches...")
        return_code, stdout, stderr = self.run_command(["git", "branch", "-a"])

        local_branches = []
        remote_branches = []

        if return_code == 0:
            lines = stdout.strip().split('\n')
            for line in lines:
                line = line.strip()
                if line.startswith('*'):
                    line = line[1:].strip()

                if '->' in line:  # Pula a linha de HEAD
                    continue

                if line.startswith('remotes/'):
                    # Remove 'remotes/' do início
                    remote_name = line[8:].strip()
                    remote_branches.append(remote_name)
                elif line:
                    local_branches.append(line)

        if self.verbose:
            self.log(
                f"Branches locais: {', '.join(local_branches) if local_branches else 'Nenhuma'}")
            self.log(
                f"Branches remotas: {', '.join(remote_branches) if remote_branches else 'Nenhuma'}")

        return local_branches, remote_branches

    def check_remote_exists(self, remote_name: str = "origin") -> bool:
        """Verifica se o remote especificado existe."""
        self.log(f"Verificando se remote '{remote_name}' existe...")
        return_code, stdout, stderr = self.run_command(["git", "remote"])

        if return_code == 0:
            remotes = [r.strip()
                       for r in stdout.strip().split('\n') if r.strip()]
            if remote_name in remotes:
                self.log(f"✓ Remote '{remote_name}' encontrado")
                return True
            else:
                self.log(
                    f"✗ Remote '{remote_name}' não encontrado. Remotes disponíveis: {', '.join(remotes)}", "ERROR")
                return False
        else:
            self.log("✗ Não foi possível listar os remotes", "ERROR")
            return False

    def get_remote_url(self, remote_name: str = "origin") -> Optional[str]:
        """Obtém a URL do remote especificado."""
        return_code, stdout, stderr = self.run_command(
            ["git", "remote", "get-url", remote_name])

        if return_code == 0:
            url = stdout.strip()
            self.log(f"✓ URL do remote '{remote_name}': {url}")
            return url
        else:
            self.log(
                f"✗ Não foi possível obter a URL do remote '{remote_name}'", "ERROR")
            return None

    def find_matching_remote_branch(self, local_branch: str) -> Optional[str]:
        """
        Encontra a branch remota correspondente à branch local.

        Tenta encontrar no formato: origin/<local_branch>
        """
        self.log(
            f"Procurando branch remota correspondente a '{local_branch}'...")

        # Primeiro, verifica a configuração upstream
        return_code, stdout, stderr = self.run_command(
            ["git", "rev-parse", "--abbrev-ref",
                f"{local_branch}@{{upstream}}"]
        )

        if return_code == 0:
            upstream = stdout.strip()
            self.log(f"✓ Upstream encontrado: {upstream}")
            return upstream

        # Se não encontrar upstream, tenta encontrar manualmente
        _, remote_branches = self.get_all_branches()

        # Procura por origin/<local_branch>
        possible_names = [
            f"origin/{local_branch}",
            f"upstream/{local_branch}",
            local_branch  # Caso a branch remota tenha o mesmo nome
        ]

        for remote_branch in remote_branches:
            for possible in possible_names:
                if remote_branch == possible or remote_branch.endswith(f"/{possible}"):
                    self.log(
                        f"✓ Branch remota correspondente encontrada: {remote_branch}")
                    return remote_branch

        self.log(
            f"✗ Não foi encontrada uma branch remota correspondente para '{local_branch}'", "WARNING")

        # Tenta encontrar a branch padrão (main ou master)
        for default in ["main", "master"]:
            if f"origin/{default}" in remote_branches:
                self.log(f"Usando branch padrão: origin/{default}")
                return f"origin/{default}"

        return None

    def check_for_uncommitted_changes(self) -> Tuple[bool, str]:
        """Verifica se há alterações não commitadas."""
        self.log("Verificando alterações não commitadas...")
        return_code, stdout, stderr = self.run_command(
            ["git", "status", "--porcelain"])

        if return_code == 0:
            if stdout.strip():
                changes = stdout.strip().split('\n')
                self.log(
                    f"✓ Encontradas {len(changes)} alterações não commitadas")
                return True, stdout
            else:
                self.log("✓ Nenhuma alteração não commitada encontrada")
                return False, ""
        else:
            self.log("✗ Erro ao verificar alterações", "ERROR")
            return False, ""

    def discard_all_changes(self) -> bool:
        """Descarta todas as alterações locais."""
        self.log("Descartando todas as alterações locais...")

        # Primeiro, descarta alterações em arquivos rastreados
        return_code, stdout, stderr = self.run_command(
            ["git", "checkout", "--", "."])
        if return_code != 0:
            self.log("✗ Erro ao descartar alterações rastreadas", "ERROR")
            return False

        self.log("✓ Alterações rastreadas descartadas")

        # Limpa arquivos não rastreados
        return_code, stdout, stderr = self.run_command(["git", "clean", "-fd"])
        if return_code != 0:
            self.log("✗ Erro ao limpar arquivos não rastreados", "ERROR")
            return False

        self.log("✓ Arquivos não rastreados removidos")
        return True

    def fetch_remote(self, remote_name: str = "origin") -> bool:
        """Executa git fetch do remote especificado."""
        self.log(f"Executando fetch do remote '{remote_name}'...")
        return_code, stdout, stderr = self.run_command(
            ["git", "fetch", remote_name])

        if return_code == 0:
            self.log(f"✓ Fetch de '{remote_name}' concluído com sucesso")
            return True
        else:
            self.log(f"✗ Erro ao fazer fetch de '{remote_name}'", "ERROR")
            return False

    def hard_reset_to_remote(self, remote_branch: str) -> bool:
        """Executa git reset --hard para a branch remota especificada."""
        self.log(f"Executando reset --hard para '{remote_branch}'...")
        return_code, stdout, stderr = self.run_command(
            ["git", "reset", "--hard", remote_branch])

        if return_code == 0:
            self.log(f"✓ Reset --hard para '{remote_branch}' concluído")

            # Verifica o commit atual
            return_code, commit_hash, _ = self.run_command(
                ["git", "rev-parse", "--short", "HEAD"])
            if return_code == 0:
                self.log(f"✓ Agora no commit: {commit_hash.strip()}")

            return True
        else:
            self.log(
                f"✗ Erro ao executar reset --hard para '{remote_branch}'", "ERROR")
            return False

    def cleanup_remaining_files(self) -> bool:
        """Limpa quaisquer arquivos remanescentes não rastreados."""
        self.log("Limpando arquivos remanescentes...")

        # Lista arquivos não rastreados primeiro
        return_code, stdout, stderr = self.run_command(
            ["git", "clean", "-fdn"])

        if return_code == 0 and stdout.strip():
            files_to_clean = [line.strip()
                              for line in stdout.strip().split('\n') if line.strip()]
            self.log(f"Arquivos a serem removidos: {len(files_to_clean)}")

            # Remove os arquivos
            return_code, stdout, stderr = self.run_command(
                ["git", "clean", "-fd"])
            if return_code == 0:
                self.log("✓ Limpeza final concluída")
                return True
            else:
                self.log("✗ Erro na limpeza final", "WARNING")
                return False
        else:
            self.log("✓ Nenhum arquivo remanescente para limpar")
            return True

    def verify_sync(self, remote_branch: str) -> bool:
        """Verifica se o repositório local está sincronizado com o remoto."""
        self.log("Verificando sincronização...")

        # Verifica status
        return_code, stdout, stderr = self.run_command(["git", "status"])
        if return_code == 0:
            if "Your branch is up to date" in stdout or "Sua branch está atualizada" in stdout:
                self.log("✓ Branch sincronizada com o remoto")
            else:
                self.log("✗ Branch não está sincronizada", "WARNING")

        # Verifica diferenças
        return_code, stdout, stderr = self.run_command(
            ["git", "diff", remote_branch])
        if return_code == 0:
            if not stdout.strip():
                self.log("✓ Nenhuma diferença encontrada com o remoto")
                return True
            else:
                self.log("✗ Ainda há diferenças com o remoto", "ERROR")
                return False

        return True

    def execute_full_reset(self) -> bool:
        """Executa o processo completo de reset."""
        self.log("=" * 60)
        self.log("INICIANDO RESET COMPLETO PARA VERSÃO DO GITHUB")
        self.log("=" * 60)

        # 1. Verificar Git instalado
        if not self.check_git_installed():
            return False

        # 2. Verificar se é repositório Git
        if not self.check_git_repository():
            return False

        # 3. Obter branch atual
        current_branch = self.get_current_branch()
        if not current_branch:
            return False

        # 4. Verificar se remote origin existe
        if not self.check_remote_exists("origin"):
            return False

        # 5. Obter URL do remote
        remote_url = self.get_remote_url("origin")
        if not remote_url:
            self.log("Continuando sem URL do remote...", "WARNING")

        # 6. Encontrar branch remota correspondente
        remote_branch = self.find_matching_remote_branch(current_branch)
        if not remote_branch:
            self.log("Tentando usar 'origin/master' como fallback...", "WARNING")
            remote_branch = "origin/master"

        # 7. Verificar alterações não commitadas
        has_changes, changes_output = self.check_for_uncommitted_changes()

        # 8. Descartar todas as alterações
        if not self.discard_all_changes():
            return False

        # 9. Fazer fetch do remote
        if not self.fetch_remote("origin"):
            return False

        # 10. Reset hard para a branch remota
        if not self.hard_reset_to_remote(remote_branch):
            return False

        # 11. Limpeza final
        if not self.cleanup_remaining_files():
            self.log(
                "Alguns problemas na limpeza final, mas continuando...", "WARNING")

        # 12. Verificar sincronização
        if not self.verify_sync(remote_branch):
            self.log("Verificação de sincronização falhou", "WARNING")

        self.log("=" * 60)
        self.log("✓ RESET COMPLETO CONCLUÍDO COM SUCESSO!")
        self.log(f"✓ Branch: {current_branch}")
        self.log(f"✓ Sincronizado com: {remote_branch}")
        if remote_url:
            self.log(f"✓ Remote: {remote_url}")
        self.log("=" * 60)

        return True

    def print_summary(self):
        """Imprime um resumo do estado atual."""
        print("\n" + "=" * 60)
        print("RESUMO DO REPOSITÓRIO")
        print("=" * 60)

        # Branch atual
        return_code, branch, _ = self.run_command(
            ["git", "branch", "--show-current"])
        if return_code == 0:
            print(f"📌 Branch atual: {branch.strip()}")

        # Último commit
        return_code, commit, _ = self.run_command(
            ["git", "log", "--oneline", "-1"])
        if return_code == 0:
            print(f"📝 Último commit: {commit.strip()}")

        # Status
        return_code, status, _ = self.run_command(["git", "status", "--short"])
        if return_code == 0:
            if status.strip():
                print(
                    f"📋 Alterações pendentes: {len(status.strip().split(chr(10)))} arquivo(s)")
            else:
                print("✅ Repositório limpo")

        # Remote
        return_code, remote, _ = self.run_command(["git", "remote", "-v"])
        if return_code == 0:
            print(f"🌐 Remotes:\n{remote}")

        print("=" * 60)


def main():
    """Função principal."""
    parser = argparse.ArgumentParser(
        description="Reset completo do repositório local para a versão do GitHub",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  %(prog)s                    # Reset completo sem confirmações
  %(prog)s --dry-run          # Apenas mostra o que seria feito
  %(prog)s --quiet            # Executa sem output detalhado
  %(prog)s --no-force         # Pede confirmação antes de executar
        """
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Apenas mostra o que seria feito, não executa"
    )

    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Executa em modo silencioso"
    )

    parser.add_argument(
        "--no-force",
        action="store_true",
        help="Pede confirmação antes de executar comandos perigosos"
    )

    parser.add_argument(
        "--summary",
        action="store_true",
        help="Apenas mostra um resumo do repositório"
    )

    args = parser.parse_args()

    # Criar instância do automator
    automator = GitResetAutomator(
        verbose=not args.quiet,
        force=not args.no_force
    )

    if args.summary:
        automator.print_summary()
        return 0

    if args.dry_run:
        print("🚧 MODO DRY-RUN - Nenhum comando será executado")
        print("Comandos que seriam executados:")
        print("1. git checkout -- .")
        print("2. git clean -fd")
        print("3. git fetch origin")
        print("4. git reset --hard origin/<sua-branch>")
        print("5. git clean -fd (novamente para limpeza final)")
        return 0

    if not args.no_force:
        print("⚠️  ATENÇÃO: Este script vai descartar TODAS as alterações locais!")
        print("⚠️  Não há como desfazer esta ação!")
        print("=" * 60)

        # Verifica se há alterações não commitadas primeiro
        automator.check_git_repository()
        has_changes, _ = automator.check_for_uncommitted_changes()

        if has_changes:
            print("❌ Há alterações não commitadas que serão PERDIDAS!")

        confirm = input(
            "Tem certeza que deseja continuar? (digite 'SIM' para confirmar): ")
        if confirm.upper() != "SIM":
            print("Operação cancelada.")
            return 1

    # Executar o reset completo
    try:
        success = automator.execute_full_reset()
        if success:
            # Mostrar resumo final
            automator.print_summary()
            return 0
        else:
            print("❌ Reset falhou!")
            return 1
    except KeyboardInterrupt:
        print("\n\n⏹️  Operação interrompida pelo usuário")
        return 1
    except Exception as e:
        print(f"\n\n💥 Erro inesperado: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
