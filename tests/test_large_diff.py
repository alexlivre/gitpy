import os
import sys
import shutil
import subprocess
import time

# Configuração
TEST_DIR = "temp_test_large"
APP_DIR = os.getcwd()
PYTHON_EXE = sys.executable

RESET = "\033[0m"
YELLOW = "\033[93m"
GREEN = "\033[92m"
RED = "\033[91m"

def log(msg, color=RESET):
    print(f"{color}[TEST] {msg}{RESET}")

def run_cmd(cmd, cwd):
    env = os.environ.copy()
    env["PYTHONPATH"] = APP_DIR
    env["PYTHONIOENCODING"] = "utf-8"
    return subprocess.run(
        cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", env=env
    )

def setup():
    if os.path.exists(TEST_DIR):
        subprocess.run(["cmd", "/c", f"rd /s /q {TEST_DIR}"], capture_output=True)
    os.makedirs(TEST_DIR)
    
    run_cmd(["git", "init"], TEST_DIR)
    run_cmd(["git", "config", "user.email", "test@bot.com"], TEST_DIR)
    run_cmd(["git", "config", "user.name", "Test Bot"], TEST_DIR)

def create_large_file():
    log("Creating large file (approx 150KB)...", YELLOW)
    file_path = os.path.join(TEST_DIR, "large_file.py")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("# Large Auto-Generated File\n")
        for i in range(5000):
            f.write(f"def function_{i}():\n    print('This is a filler line number {i} to increase file size.')\n    return {i} * {i}\n\n")
    
    log("Staging large file...", YELLOW)
    run_cmd(["git", "add", "."], TEST_DIR)
    
    return file_path

def test_large_diff_handing():
    setup()
    create_large_file()
    
    log("Running GitPy default flow (Dry Run)...", YELLOW)
    # Usamos --dry-run para não commitar de verdade, queremos ver o output do diff
    # Usamos --debug para ver os logs internos do scanner
    cmd = [PYTHON_EXE, os.path.join(APP_DIR, "launcher.py"), "main", "--path", TEST_DIR, "--yes", "--dry-run", "--debug"]
    
    res = run_cmd(cmd, APP_DIR)
    
    output = res.stdout + res.stderr
    
    with open("test_large_diff_result.txt", "w", encoding="utf-8") as f:
        if "Vibe Vault" in output or "Smart Pack" in output or "Diff truncado" in output:
            log("✅ Vibe Vault Activated! (Smart Packing works)", GREEN)
            f.write("PASS: Vibe Vault Activated")
        else:
            log("⚠️ Vibe Vault NOT detected in output.", YELLOW)
            f.write("FAIL: Vibe Vault NOT detected")
            f.write("\n--- OUTPUT ---\n")
            f.write(output)

    # Check if execution finished gracefully
    if res.returncode == 0:
        log("Execution finished successfully.", GREEN)
    else:
        log(f"Execution failed with RC {res.returncode}", RED)
        print(res.stderr)

if __name__ == "__main__":
    test_large_diff_handing()
