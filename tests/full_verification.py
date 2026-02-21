import os
import sys
import shutil
import subprocess
import time
import re
from typing import List, Tuple

# Configuração
REPO_URL = "https://github.com/alexlivre/TEST_PLAN.git"
TEST_DIR = "temp_test_execution"
APP_DIR = os.getcwd()
PYTHON_EXE = sys.executable

# Cores para o terminal
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"

def log(msg, color=RESET):
    print(f"{color}[TEST] {msg}{RESET}")

def run_cmd(cmd: List[str], cwd: str, expect_fail=False) -> Tuple[bool, str, str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = APP_DIR
    env["PYTHONIOENCODING"] = "utf-8"
    
    # Adiciona flag --debug para capturar detalhes internos se for comando do gitpy
    if "launcher.py" in cmd:
        if "--debug" not in cmd:
            cmd.append("--debug")

    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=env,
            timeout=60
        )
        success = result.returncode == 0
        if expect_fail:
            success = not success
            
        return success, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def setup():
    log("Cleaning up previous runs...", YELLOW)
    if os.path.exists(TEST_DIR):
        # Retry logic for Windows file locking
        for _ in range(3):
            try:
                shutil.rmtree(TEST_DIR)
                break
            except:
                time.sleep(1)
        if os.path.exists(TEST_DIR):
             # Fallback to shell command
             subprocess.run(["cmd", "/c", f"rd /s /q {TEST_DIR}"], capture_output=True)

    os.makedirs(TEST_DIR)
    
    log(f"Cloning repository {REPO_URL}...", YELLOW)
    success, out, err = run_cmd(["git", "clone", REPO_URL, "."], TEST_DIR)
    if not success:
        log(f"Clone failed: {err}", RED)
        sys.exit(1)
    
    # Configure Git Identity for tests
    run_cmd(["git", "config", "user.email", "test-bot@gitpy.com"], TEST_DIR)
    run_cmd(["git", "config", "user.name", "GitPy Test Bot"], TEST_DIR)

def test_infra_scanner():
    log("\n--- 1. Testing Infrastructure (Scanner) ---", YELLOW)
    
    # Cenário: Repo Limpo
    cmd = [PYTHON_EXE, os.path.join(APP_DIR, "launcher.py"), "main", "--path", TEST_DIR, "--yes"]
    success, out, err = run_cmd(cmd, APP_DIR)
    
    if "Working tree clean" in out or "Working tree clean" in err: # Pode sair no stderr se for log
        log("✅ Working Tree Clean detected correctly", GREEN)
    else:
        log("❌ Failed to detect clean tree", RED)
        print(out)

def test_security_blocklist():
    log("\n--- 2. Testing Security (Blocklist) ---", YELLOW)
    
    # Criar arquivo .env
    env_path = os.path.join(TEST_DIR, ".env")
    with open(env_path, "w") as f:
        f.write("SECRET=123")
    
    # Tentar commitar
    cmd = [PYTHON_EXE, os.path.join(APP_DIR, "launcher.py"), "main", "--path", TEST_DIR, "--yes", "--model", "groq"]
    # Esperamos que o gitpy detecte, mas o blocklist geralmente impede isso silenciosamente ou com erro.
    # No caso atual, o Scanner ignora? Ou o Sanitizer bloqueia?
    # O gitpy usa 'git add -A'. O scan vai pegar. O sanitizer deve rodar depois?
    # Vamos ver o output.
    
    # OBS: O gitpy atual faz 'Add -A' ANTES do sanitizer no fluxo --yes? 
    # Não, o Brain roda antes do Executor. O Brain chama o Sanitizer/Redactor.
    # Mas se o 'Add -A' é feito no Executor, o arquivo é staged.
    # A 'Muralha de Chumbo' (dlc.py) deve impedir o processamento no brain?
    # Vamos verificar o comportamento.
    
    success, out, err = run_cmd(cmd, APP_DIR)
    
    # Se o sistema for robusto, ele não deve incluir o .env no commit, ou deve falhar.
    # Verificamos se o arquivo foi commitado.
    is_committed = subprocess.run(["git", "ls-files", ".env"], cwd=TEST_DIR, capture_output=True, text=True).stdout.strip()
    
    if is_committed:
        log("❌ SECURITY FAIL: .env was committed!", RED)
    else:
        log("✅ SECURITY PASS: .env was NOT committed (or blocked)", GREEN)

def test_security_redactor():
    log("\n--- 3. Testing Security (Redactor) ---", YELLOW)
    
    # Criar arquivo com segredo
    secret_file = os.path.join(TEST_DIR, "leaky_code.py")
    with open(secret_file, "w") as f:
        f.write("api_key = 'sk-1234567890abcdef1234567890abcdef'") # Fake OpenAI key
        
    cmd = [PYTHON_EXE, os.path.join(APP_DIR, "launcher.py"), "main", "--path", TEST_DIR, "--yes", "--message", "feat: adiciona segredo", "--model", "groq"]
    success, out, err = run_cmd(cmd, APP_DIR)
    
    if success:
        log("✅ Commit successful", GREEN)
        # Verificar o log do commit para ver se a IA mencionou o segredo OU se o diff enviado foi redactado.
        # Difícil validar o que foi enviado pra IA sem interceptar, mas podemos ver se o 'debug' mostra [REDACTED]
        if "[REDACTED:Generic_Token]" in out or "[REDACTED:Generic_Token]" in err:
            log("✅ Redactor active: Found [REDACTED] tag in logs", GREEN)
        else:
            log("⚠️ Redactor warning: Could not verify [REDACTED] tag in output", YELLOW)
    else:
        log(f"❌ Commit failed: {err}", RED)

def test_e2e_flow():
    log("\n--- 4. Testing End-to-End ---", YELLOW)
    
    filename = "feature_test.txt"
    filepath = os.path.join(TEST_DIR, filename)
    with open(filepath, "w") as f:
        f.write(f"E2E Test Run at {time.ctime()}")
        
    cmd = [PYTHON_EXE, os.path.join(APP_DIR, "launcher.py"), "main", "--path", TEST_DIR, "--yes", "--message", "feat: teste e2e automatizado", "--model", "groq"]
    success, out, err = run_cmd(cmd, APP_DIR)
    
    if success:
        log("✅ E2E Commit & Push executed", GREEN)
        
        # Verificar git log
        log_res = subprocess.run(["git", "log", "-1", "--pretty=%s"], cwd=TEST_DIR, capture_output=True, text=True).stdout.strip()
        log(f"Commit Message: {log_res}", GREEN)
        
        if "feat:" in log_res or "teste" in log_res:
             log("✅ Commit message matches context", GREEN)
        else:
             log("⚠️ Commit message might be generic", YELLOW)
    else:
        log(f"❌ E2E Failed: {err}", RED)

def main():
    try:
        setup()
        test_infra_scanner()
        test_security_blocklist()
        test_security_redactor()
        test_e2e_flow()
        log("\n🏁 All tests completed.", GREEN)
    except Exception as e:
        log(f"Test Suite Crashed: {e}", RED)

if __name__ == "__main__":
    main()
