"""
Super Test Runner - GitPy Definitive Validation (GitHub Edition)
================================================================
Tests all features of GitPy against a REAL GitHub repository.
All commits are pushed to: https://github.com/alexlivre/supertestes.git
Logs results to super_test_debug.log.
"""
import os
import sys
import shutil
import subprocess
import json
import time

# --- Configuration ---
REPO_URL = "https://github.com/alexlivre/supertestes.git"
TEST_WORKSPACE = os.path.abspath("temp_super_test")
APP_DIR = os.path.abspath(os.getcwd())
GITPY_CMD = [sys.executable, os.path.join(APP_DIR, "launcher.py")]

# Color codes
RESET = "\033[0m"
BOLD = "\033[1m"
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
CYAN = "\033[96m"

LOG_FILE = os.path.join(APP_DIR, "super_test_debug.log")
RESULTS = {"pass": 0, "fail": 0, "skip": 0}

# ========= HELPERS =========

def log(msg, color=RESET, header=False):
    prefix = "\n>>> " if header else "  "
    style = BOLD if header else ""
    print(f"{style}{color}{prefix}{msg}{RESET}")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{prefix.strip()} {msg}\n")

def result(name, passed, skip=False):
    if skip:
        RESULTS["skip"] += 1
        log(f"⏭️  SKIP: {name}", YELLOW)
    elif passed:
        RESULTS["pass"] += 1
        log(f"✅ PASS: {name}", GREEN)
    else:
        RESULTS["fail"] += 1
        log(f"❌ FAIL: {name}", RED)

def run(cmd, cwd=None, input_str=None, timeout=120):
    """Runs a command. Returns (returncode, stdout, stderr)."""
    if isinstance(cmd, str) and cmd.startswith("gitpy"):
        parts = cmd.split()
        full_cmd = GITPY_CMD + parts[1:]
    elif isinstance(cmd, list):
        full_cmd = cmd
    else:
        full_cmd = cmd.split()

    log(f"$ {' '.join(full_cmd)}", CYAN)

    try:
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        
        r = subprocess.run(
            full_cmd, cwd=cwd, input=input_str,
            capture_output=True, text=True, encoding='utf-8',
            errors='replace', timeout=timeout, env=env
        )
        stdout = r.stdout or ""
        stderr = r.stderr or ""

        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"  [STDOUT] {stdout[:3000]}\n")
            f.write(f"  [STDERR] {stderr[:3000]}\n")
            f.write(f"  [EXIT {r.returncode}]\n")

        return r.returncode, stdout, stderr
    except subprocess.TimeoutExpired:
        log("TIMEOUT!", RED)
        return -1, "", "TIMEOUT"
    except Exception as e:
        log(f"EXCEPTION: {e}", RED)
        return -1, "", str(e)

def git(args, cwd):
    """Shorthand for git commands."""
    return run(["git"] + args, cwd=cwd)

def git_push(cwd, force=False):
    """Push to GitHub."""
    args = ["push", "origin", "main"]
    if force:
        args.append("--force")
    rc, out, err = git(args, cwd)
    if rc == 0:
        log("📤 Pushed to GitHub!", GREEN)
    else:
        log(f"⚠️ Push failed: {err}", YELLOW)
    return rc

# ========= SETUP =========

def setup():
    log("SETUP: Preparing workspace & cloning from GitHub", YELLOW, header=True)

    # Clean
    if os.path.exists(TEST_WORKSPACE):
        for _ in range(5):
            try:
                shutil.rmtree(TEST_WORKSPACE)
                break
            except PermissionError:
                time.sleep(2)
    os.makedirs(TEST_WORKSPACE)

    # Clear previous log
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.write("=== Super Test Log (GitHub Edition) ===\n")

    # Clone
    repo_dir = os.path.join(TEST_WORKSPACE, "supertestes")
    rc, _, _ = run(["git", "clone", REPO_URL, repo_dir])
    if rc != 0:
        log("Clone failed!", RED)
        return None

    # Configure git identity
    git(["config", "user.email", "test@gitpy.dev"], repo_dir)
    git(["config", "user.name", "GitPy SuperTest Bot"], repo_dir)

    # ALWAYS reset to a fresh state (orphan branch)
    log("🔄 Resetting repo to fresh state...", YELLOW)
    git(["checkout", "--orphan", "fresh"], repo_dir)
    # Remove all tracked files
    git(["rm", "-rf", "."], repo_dir)
    
    # Create initial README
    readme_path = os.path.join(repo_dir, "README.md")
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write("# 🧪 Super Testes GitPy\n\n")
        f.write("Este repositório é usado para validar todas as funcionalidades do GitPy.\n\n")
        f.write("**Gerado automaticamente pelo Super Test Runner.**\n")
    git(["add", "-A"], repo_dir)
    git(["commit", "-m", "🏗️ chore: initial setup for GitPy testing"], repo_dir)
    
    # Rename branch to main and force push
    git(["branch", "-M", "main"], repo_dir)
    rc_push = git_push(repo_dir, force=True)
    if rc_push != 0:
        log("Cannot push to GitHub! Check credentials.", RED)
        return None
    
    log(f"✅ Repo ready at: {repo_dir}", GREEN)
    return repo_dir

# ========= TESTS =========

def test_init(repo_dir):
    # DEPRECATED: gitpy init was removed
    pass

def test_ignore_add(repo_dir):
    # DEPRECATED: tool-ignore is internal now, explicit command removed from regression suite usage
    pass

def test_ignore_scan(repo_dir):
    # DEPRECATED: .gitpy config for ignore scan removed
    pass

def test_security_blocklist(repo_dir):
    log("TEST 3: Security Blocklist (Muralha de Chumbo)", BLUE, header=True)

    # Create .env (forbidden file)
    env_path = os.path.join(repo_dir, ".env")
    with open(env_path, "w") as f:
        f.write("API_KEY=sk-FAKE-1234567890abcdef-TEST-ONLY")

    # Stage it
    git(["add", ".env"], repo_dir)

    # gitpy should BLOCK this with exit 1
    rc, out, err = run("gitpy --yes --dry-run", cwd=repo_dir)
    blocked = rc == 1
    result("Security blocked .env (Exit 1)", blocked)
    
    has_bloqueio = "BLOQUEIO" in out or "blocked" in out.lower()
    result("Security showed BLOQUEIO message", has_bloqueio)

    # Cleanup — unstage and remove .env
    git(["reset", "HEAD", ".env"], repo_dir)
    if os.path.exists(env_path):
        os.remove(env_path)

def test_dry_run(repo_dir):
    log("TEST 4: Dry Run (--dry-run)", BLUE, header=True)

    # Create a meaningful change
    app_path = os.path.join(repo_dir, "app.py")
    with open(app_path, "w") as f:
        f.write('"""GitPy Test Application."""\n\ndef main():\n    print("Hello from GitPy SuperTest!")\n\nif __name__ == "__main__":\n    main()\n')
    git(["add", "-A"], repo_dir)

    # Record HEAD before dry run
    _, head_before, _ = git(["rev-parse", "HEAD"], repo_dir)

    rc, out, err = run("gitpy --yes --dry-run --model groq", cwd=repo_dir)

    # Dry run should succeed but NOT commit
    result("Dry run executed (no crash)", rc == 0)

    # Check that no commit was actually made (HEAD unchanged)
    _, head_after, _ = git(["rev-parse", "HEAD"], repo_dir)
    result("Dry run did NOT commit", head_before.strip() == head_after.strip())

def test_ninja_commit(repo_dir):
    log("TEST 5: Ninja Commit (--yes) + Push to GitHub", BLUE, header=True)

    # Check for API key
    env_path = os.path.join(APP_DIR, ".env")
    has_key = os.path.exists(env_path)
    if not has_key:
        result("Ninja commit (no API key)", False, skip=True)
        return

    # app.py should still be staged from dry_run test
    # If not, re-stage
    git(["add", "-A"], repo_dir)

    # Run gitpy --yes which should: generate commit msg + commit + push
    rc, out, err = run("gitpy --yes --model groq", cwd=repo_dir)
    
    committed = rc == 0
    result("Ninja commit + push succeeded", committed)
    
    if committed:
        # Verify commit exists
        _, log_out, _ = git(["log", "--oneline", "-3"], repo_dir)
        log(f"📋 Recent commits: {log_out}", GREEN)

def test_vibe_vault(repo_dir):
    log("TEST 6: Vibe Vault (Large Diff > 100KB)", BLUE, header=True)

    # Create a large file (200KB)
    large_path = os.path.join(repo_dir, "large_generated_data.txt")
    with open(large_path, "w") as f:
        for i in range(15000):
            f.write(f"// Line {i}: Generated test data for Vibe Vault validation\n")
    git(["add", "-A"], repo_dir)

    # Run with dry-run to check vault activation without committing
    rc, out, err = run("gitpy --yes --dry-run --model groq", cwd=repo_dir)

    vault_activated = "Vibe Vault" in out or "Diff muito grande" in out or "sumarizada" in out
    result("Vibe Vault activated for large diff", vault_activated)
    
    # Now do a real commit+push with the large file
    git(["add", "-A"], repo_dir)
    rc2, out2, err2 = run("gitpy --yes --model groq", cwd=repo_dir)
    result("Vibe Vault commit + push", rc2 == 0)

def test_scaffolder(repo_dir):
    log("TEST 7: Scaffolder (gitpy new)", BLUE, header=True)
    
    # Create a new project INSIDE the test repo so it gets pushed
    rc, out, err = run("gitpy new meu-projeto --type python", cwd=repo_dir)
    
    project_dir = os.path.join(repo_dir, "meu-projeto")
    created = os.path.isdir(project_dir)
    result("gitpy new created project dir", created)
    
    if created:
        # Check files
        has_main = os.path.exists(os.path.join(project_dir, "main.py"))
        result("Scaffold has main.py", has_main)
        
        # Commit & Push the scaffolded project
        git(["add", "-A"], repo_dir)
        git(["commit", "-m", "🏗️ feat: scaffold meu-projeto via gitpy new"], repo_dir)
        git_push(repo_dir)

def test_context_hint(repo_dir):
    log("TEST 8: Context Hint (-m flag)", BLUE, header=True)
    
    # Create a change
    with open(os.path.join(repo_dir, "utils.py"), "w") as f:
        f.write('"""Utility functions for testing."""\n\ndef add(a, b):\n    return a + b\n\ndef multiply(a, b):\n    return a * b\n')
    git(["add", "-A"], repo_dir)
    
    # Run with context hint - use list to preserve quoted argument
    cmd = GITPY_CMD + ["--yes", "--model", "groq", "-m", "adicionando funções utilitárias"]
    log(f"$ {' '.join(cmd)}", CYAN)
    
    try:
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        r = subprocess.run(
            cmd, cwd=repo_dir,
            capture_output=True, text=True, encoding='utf-8',
            errors='replace', timeout=120, env=env
        )
        stdout = r.stdout or ""
        stderr = r.stderr or ""
        
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"  [STDOUT] {stdout[:3000]}\n")
            f.write(f"  [STDERR] {stderr[:3000]}\n")
            f.write(f"  [EXIT {r.returncode}]\n")
        
        result("Context hint (-m) commit succeeded", r.returncode == 0)
    except Exception as e:
        log(f"EXCEPTION: {e}", RED)
        result("Context hint (-m) commit succeeded", False)

# ========= FINAL VERIFICATION =========

def verify_github(repo_dir):
    log("FINAL: Verifying GitHub state", BLUE, header=True)
    
    # Pull to confirm remote is in sync
    rc, out, err = git(["log", "--oneline", "-10"], repo_dir)
    log(f"📋 All commits on GitHub:\n{out}", GREEN)
    
    # Count commits
    _, count_out, _ = git(["rev-list", "--count", "HEAD"], repo_dir)
    log(f"📊 Total commits: {count_out.strip()}", GREEN)

# ========= MAIN =========

def print_summary():
    log("", header=True)
    log("=" * 60, BOLD)
    total = RESULTS["pass"] + RESULTS["fail"] + RESULTS["skip"]
    color = GREEN if RESULTS["fail"] == 0 else RED
    log(f"RESULTS: {RESULTS['pass']}/{total} passed, {RESULTS['fail']} failed, {RESULTS['skip']} skipped", 
        color, header=True)
    log("=" * 60, BOLD)
    log(f"📂 Full log: {LOG_FILE}", BLUE)
    log(f"🌐 GitHub: {REPO_URL}", BLUE)

def main():
    repo_dir = setup()
    if not repo_dir:
        log("Setup failed. Aborting.", RED)
        return

    # Phase 1: Init & Config (DEPRECATED)
    # test_init(repo_dir)
    # test_ignore_add(repo_dir)
    # test_ignore_scan(repo_dir)

    # Phase 2: Security
    test_security_blocklist(repo_dir)

    # Phase 3: Core Workflow (with real GitHub push)
    test_dry_run(repo_dir)
    test_ninja_commit(repo_dir)

    # Phase 4: Vibe Vault
    test_vibe_vault(repo_dir)

    # Phase 5: Tools
    test_scaffolder(repo_dir)
    test_context_hint(repo_dir)

    # Final
    verify_github(repo_dir)
    print_summary()

if __name__ == "__main__":
    main()
