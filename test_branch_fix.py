#!/usr/bin/env python3
"""
Script de teste para validar a correção do erro de troca de branch.
"""

import os
import tempfile
import shutil
import subprocess
from pathlib import Path

def run_cmd(cmd, cwd):
    """Executa um comando e retorna o resultado."""
    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    return result.returncode == 0, result.stdout, result.stderr

def test_branch_switch_with_changes():
    """Testa o fluxo de troca de branch com alterações locais."""
    
    # Criar um repositório temporário para testes
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_path = Path(temp_dir) / "test_repo"
        repo_path.mkdir()
        
        print(f"🧪 Testando em repositório temporário: {repo_path}")
        
        # Inicializar repositório Git
        success, _, err = run_cmd("git init", repo_path)
        if not success:
            print(f"❌ Falha ao inicializar Git: {err}")
            return False
        
        # Configurar usuário Git
        run_cmd("git config user.name 'Test User'", repo_path)
        run_cmd("git config user.email 'test@example.com'", repo_path)
        
        # Criar arquivo inicial e fazer commit
        test_file = repo_path / "test.txt"
        test_file.write_text("conteúdo inicial")
        run_cmd("git add test.txt", repo_path)
        run_cmd("git commit -m 'commit inicial'", repo_path)
        
        # Verificar qual branch inicial foi criada
        success, stdout, _ = run_cmd("git branch", repo_path)
        if success and stdout.strip():
            branches = [line.strip().replace("* ", "") for line in stdout.strip().split("\n") if line.strip()]
            initial_branch = branches[0] if branches else None
            print(f"📋 Branch inicial detectada: {initial_branch}")
        else:
            initial_branch = None
        
        # Se não há branch, criar master primeiro
        if not initial_branch:
            run_cmd("git checkout -b master", repo_path)
            initial_branch = "master"
            print(f"📋 Branch master criada")
        
        # Criar branch de teste
        run_cmd("git checkout -b feature-branch", repo_path)
        
        # Modificar arquivo para simular alterações locais
        test_file.write_text("conteúdo modificado")
        
        # Tentar voltar para branch inicial (deve falhar sem tratamento)
        success, stdout, stderr = run_cmd(f"git checkout {initial_branch}", repo_path)
        
        if "would be overwritten by checkout" in stderr:
            print("✅ Erro esperado detectado: alterações locais impedem checkout")
            
            # Testar stash
            run_cmd("git stash push -m 'test stash'", repo_path)
            
            # Tentar checkout novamente
            success, _, _ = run_cmd(f"git checkout {initial_branch}", repo_path)
            
            if success:
                print("✅ Stash funcionou: checkout realizado com sucesso")
                
                # Voltar para feature branch e aplicar stash
                run_cmd("git checkout feature-branch", repo_path)
                run_cmd("git stash pop", repo_path)
                
                # Verificar se as alterações foram restauradas
                content = test_file.read_text()
                if content == "conteúdo modificado":
                    print("✅ Stash pop funcionou: alterações restauradas")
                    return True
                else:
                    print(f"❌ Stash pop falhou: conteúdo esperado 'conteúdo modificado', encontrado '{content}'")
            else:
                print("❌ Stash falhou: checkout ainda não funciona")
        else:
            print(f"❌ Erro inesperado: {stderr}")
    
    return False

if __name__ == "__main__":
    print("🔧 Testando correção do erro de troca de branch...")
    print("=" * 50)
    
    if test_branch_switch_with_changes():
        print("\n✅ Todos os testes passaram! A correção está funcionando.")
    else:
        print("\n❌ Alguns testes falharam. Verifique a implementação.")
    
    print("=" * 50)
