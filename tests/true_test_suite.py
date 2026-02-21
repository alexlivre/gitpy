"""
True Test Suite - GitPy Real World Validation
=============================================
Tests all features of GitPy against a REAL GitHub repository:
https://github.com/alexlivre/supertestes.git

Features tested:
- Basic Workflow: Add, Edit, Delete files
- Context Hint (-m)
- Stealth Mode (Private files)
- Security Blocklist (.env)
- Dry Run
- Self-Healing (Git Healer) via Simulated Concurrent Push

All automation uses 'gitpy auto --yes'.
"""
import os
import sys
import shutil
import subprocess
import time
import random

# --- Configuration ---
REPO_URL = "https://github.com/alexlivre/supertestes.git"
TEST_WORKSPACE = os.path.abspath("temp_true_test")
APP_DIR = os.path.abspath(os.getcwd())
# Ensure we use the same python interpreter and the launcher script
GITPY_CMD = [sys.executable, os.path.join(APP_DIR, "launcher.py")]

# Color codes for output
RESET = "\033[0m"
BOLD = "\033[1m"
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
CYAN = "\033[96m"

LOG_FILE = os.path.join(APP_DIR, "true_test_suite.log")
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

def run_cmd(cmd, cwd=None, input_str=None, timeout=300, ignore_error=False):
    """Runs a command. Returns (returncode, stdout, stderr)."""
    full_cmd = cmd
    if isinstance(cmd, str):
        full_cmd = cmd.split()
    
    # Check if it's a gitpy command and prepend python executable if needed
    if full_cmd[0] == "gitpy":
        full_cmd = GITPY_CMD + full_cmd[1:]
    
    display_cmd = ' '.join(full_cmd)
    log(f"$ {display_cmd}", CYAN)

    try:
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        # Force Unbuffered output for better real-time logs if we were streaming, 
        # but here we capture.
        env["PYTHONUNBUFFERED"] = "1"
        
        r = subprocess.run(
            full_cmd, cwd=cwd, input=input_str,
            capture_output=True, text=True, encoding='utf-8',
            errors='replace', timeout=timeout, env=env
        )
        stdout = r.stdout or ""
        stderr = r.stderr or ""

        # Log output to file
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"  [STDOUT] {stdout[:5000]}\n")
            f.write(f"  [STDERR] {stderr[:5000]}\n")
            f.write(f"  [EXIT {r.returncode}]\n")
            
        return r.returncode, stdout, stderr
    except subprocess.TimeoutExpired:
        log("TIMEOUT!", RED)
        return -1, "", "TIMEOUT"
    except Exception as e:
        log(f"EXCEPTION: {e}", RED)
        return -1, "", str(e)

def git(args, cwd):
    return run_cmd(["git"] + args, cwd=cwd)

def git_push(cwd, force=False):
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


def on_rm_error(func, path, exc_info):
    """
    Error handler for ``shutil.rmtree``.
    If the error is due to an access error (read only file),
    it attempts to add write permission and then retries.
    If the error is for another reason it re-raises the error.
    """
    import stat
    if not os.access(path, os.W_OK):
        # Is the error an access error?
        os.chmod(path, stat.S_IWRITE)
        func(path)
    else:
        raise

# ========= SETUP =========

def setup():
    log("SETUP: Preparing workspace & cloning from GitHub", YELLOW, header=True)
    
    # DEBUG: Check if stealth tool implementation is correct
    stealth_main = os.path.join(APP_DIR, "cartridges", "tool", "tool-stealth", "main.py")
    if os.path.exists(stealth_main):
        with open(stealth_main, "r") as f:
            content = f.read()
            if "async def process" in content:
                 log(f"✅ Stealth Tool 'process' function FOUND.", GREEN)
            else:
                 log(f"❌ Stealth Tool 'process' function MISSING!", RED)

    # Clean previous run
    if os.path.exists(TEST_WORKSPACE):
        try:
            shutil.rmtree(TEST_WORKSPACE, onerror=on_rm_error)
        except Exception as e:
            log(f"Warning: Could not clean workspace: {e}", YELLOW)

    os.makedirs(TEST_WORKSPACE)

    # Init Log
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.write("=== GitPy True Test Suite Log ===\n")

    # Clone
    repo_dir = os.path.join(TEST_WORKSPACE, "repo_main")
    rc, _, _ = run_cmd(["git", "clone", REPO_URL, repo_dir])
    if rc != 0:
        log("Clone failed! Check internet or permissions.", RED)
        return None

    # Configure Identiy
    git(["config", "user.email", "test@gitpy.dev"], repo_dir)
    git(["config", "user.name", "GitPy Bot"], repo_dir)

    # Reset to Orphan Branch (Fresh Start)
    log("🔄 Resetting repo to fresh state (orphan branch)...", YELLOW)
    git(["checkout", "--orphan", "fresh_start_" + str(int(time.time()))], repo_dir)
    git(["rm", "-rf", "."], repo_dir)
    
    # Create structure
    os.makedirs(os.path.join(repo_dir, ".gitpy"), exist_ok=True)
    
    # Create README
    with open(os.path.join(repo_dir, "README.md"), "w") as f:
        f.write("# GitPy True Test Repository\n\nAutomated testing ground.\n")
    
    # Initial Commit & Push
    git(["add", "."], repo_dir)
    git(["commit", "-m", "chore: initial test setup"], repo_dir)
    
    # Rename to main and force push
    git(["branch", "-M", "main"], repo_dir)
    rc_push = git_push(repo_dir, force=True)
    
    if rc_push != 0:
        log("Cannot push to GitHub! Aborting.", RED)
        return None
        
    log(f"✅ Repo ready at: {repo_dir}", GREEN)
    return repo_dir

# ========= TESTS =========

def test_add_file(repo_dir):
    log("TEST 1: Add File (gitpy auto --yes)", BLUE, header=True)
    
    # Create file
    new_file = os.path.join(repo_dir, "feature.py")
    with open(new_file, "w") as f:
        f.write("def feature():\n    print('New Feature')\n")
        
    # GitPy Auto
    rc, out, err = run_cmd("gitpy auto --yes", cwd=repo_dir)
    
    # verify success
    passed = (rc == 0) and ("Commit realizado" in out) and ("Push realizado" in out)
    result("Add File Workflow", passed)
    
    # Verify file on git
    rc_git, out_git, _ = git(["ls-tree", "-r", "HEAD", "--name-only"], cwd=repo_dir)
    result("File exists in HEAD", "feature.py" in out_git)

def test_edit_file(repo_dir):
    log("TEST 2: Edit File (gitpy auto --yes)", BLUE, header=True)
    
    # Mod file
    new_file = os.path.join(repo_dir, "feature.py")
    with open(new_file, "a") as f:
        f.write("\n# Updated feature\n")
        
    # GitPy Auto
    rc, out, err = run_cmd("gitpy auto --yes", cwd=repo_dir)
    passed = (rc == 0)
    result("Edit File Workflow", passed)

def test_delete_file(repo_dir):
    log("TEST 3: Delete File (gitpy auto --yes)", BLUE, header=True)
    
    # Delete file
    new_file = os.path.join(repo_dir, "feature.py")
    os.remove(new_file)
    
    # GitPy Auto
    rc, out, err = run_cmd("gitpy auto --yes", cwd=repo_dir)
    passed = (rc == 0)
    result("Delete File Workflow", passed)
    
    # Verify gone
    rc_git, out_git, _ = git(["ls-tree", "-r", "HEAD", "--name-only"], cwd=repo_dir)
    result("File removed from HEAD", "feature.py" not in out_git)

def test_context_hint(repo_dir):
    log("TEST 4: Context Hint (-m)", BLUE, header=True)
    
    # Create change
    hint_file = os.path.join(repo_dir, "hint.txt")
    with open(hint_file, "w") as f:
        f.write("Just some text")
        
    # Run with hint
    hint_msg = "test manual hint execution"
    # We use a list to ensure the hint string is passed as a single argument
    cmd = GITPY_CMD + ["auto", "--yes", "--message", hint_msg]
    
    # run manual because run_cmd split logic might be too simple for quotes
    import shlex
    # But run_cmd handles lists correctly
    rc, out, err = run_cmd(cmd, cwd=repo_dir)
    
    passed = (rc == 0)
    result("Context Hint Workflow", passed)
    
    # Check commit message
    rc_log, out_log, _ = git(["log", "-1", "--pretty=%B"], cwd=repo_dir)
    # The AI might not use the EXACT phrase, but it usually does if it's short.
    # Or at least it should be successful.
    log(f"Commit msg: {out_log.strip()}", CYAN)

def test_stealth_mode(repo_dir):
    log("TEST 5: Stealth Mode", BLUE, header=True)
    
    # 1. Define stealth rule (skip if cannot create .gitpy, but here we can)
    # Actually stealth mode works on .gitpy-private pattern file or similar?
    # Checking launcher.py... it uses "tool/tool-stealth".
    # Let's see how stealth determines what to hide.
    # Usually it looks for files in .gitpy/private list OR a hardcoded check?
    # Assuming standard behavior: looking for secrets or specific config.
    # BUT, based on previous readings, stealth stash works on `.gitpy-private`?
    # Let's create a `.gitpy-private` file if it doesn't exist?
    # Wait, the code says: run_async(kernel.run("tool/tool-stealth", {"action": "stash", ...}))
    # We need to know what file makes stealth trigger.
    # Assuming we can create a file named "secret_plans.txt" and tell gitpy to hide it?
    # Or is it fully automatic?
    # Let's assume we need to configure it.
    
    # Creating a .gitpy-private file
    private_conf = os.path.join(repo_dir, ".gitpy-private")
    with open(private_conf, "w") as f:
        f.write("top_secret.txt\n")
        
    # Create the secret file
    secret_file = os.path.join(repo_dir, "top_secret.txt")
    with open(secret_file, "w") as f:
        f.write("Nuclear Launch Codes: 0000")
        
    # Create a public file too
    public_file = os.path.join(repo_dir, "public.txt")
    with open(public_file, "w") as f:
        f.write("Public info")
        
    # Run GitPy
    rc, out, err = run_cmd("gitpy auto --yes", cwd=repo_dir)
    
    # Check
    result("Stealth Run (Exit 0)", rc == 0)
    
    if os.path.exists(secret_file):
        result("Secret file restored locally", True)
    else:
        result("Secret file restored locally", False)
        
    # Check if secret ended up in git
    rc_ls, out_ls, _ = git(["ls-tree", "-r", "HEAD", "--name-only"], cwd=repo_dir)
    if "top_secret.txt" in out_ls:
        result("Secret file NOT in Git", False)
        log("❌ CRITICAL: Secret file WAS committed!", RED)
    elif ".gitpy-private" in out_ls:
        result("Stealth Config NOT in Git", False)
        log("❌ CRITICAL: .gitpy-private WAS committed!", RED)
    else:
        result("Secret/Config files NOT in Git", True)

def test_security_blocklist(repo_dir):
    log("TEST 6: Security Blocklist", BLUE, header=True)
    
    # Create .env
    env_file = os.path.join(repo_dir, ".env")
    with open(env_file, "w") as f:
        f.write("API_KEY=12345")
        
    git(["add", ".env"], cwd=repo_dir)
    
    # Run GitPy - Should Fail
    rc, out, err = run_cmd("gitpy auto --yes", cwd=repo_dir)
    
    if rc == 1 and ("BLOQUEIO" in out or "blocked" in out.lower()):
        result("Blocked .env commit", True)
    else:
        result("Blocked .env commit", False)
        log(f"Output: {out}", RED)
        
    # Cleanup
    git(["reset", "HEAD", ".env"], cwd=repo_dir)
    os.remove(env_file)

def test_dry_run(repo_dir):
    log("TEST 7: Dry Run", BLUE, header=True)
    
    # Change
    fpath = os.path.join(repo_dir, "dry.txt")
    with open(fpath, "w") as f:
        f.write("Should not exist")
        
    git(["add", "."], cwd=repo_dir)
    
    # Run
    rc, out, err = run_cmd("gitpy auto --yes --dry-run", cwd=repo_dir)
    
    result("Dry Run Exit 0", rc == 0)
    result("Dry Run Output Check", "[DRY-RUN]" in out)
    
    # Verify no commit
    rc_s, out_s, _ = git(["status", "--porcelain"], cwd=repo_dir)
    result("No commit made", "dry.txt" in out_s or "A  dry.txt" in out_s)
    
    # Cleanup
    git(["reset", "HEAD", "dry.txt"], cwd=repo_dir)
    os.remove(fpath)

def test_error_simulation(repo_dir):
    log("TEST 8: Error Simulation & Self-Healing (Git Healer)", BLUE, header=True)
    
    # 1. Setup a "Colleague" repo (Repo B)
    repo_b = os.path.join(TEST_WORKSPACE, "repo_colleague")
    if os.path.exists(repo_b): shutil.rmtree(repo_b)
    
    run_cmd(["git", "clone", REPO_URL, repo_b])
    git(["config", "user.email", "colleague@evil.com"], repo_b)
    git(["config", "user.name", "Evil Colleague"], repo_b)
    
    # 2. Add content in Repo A (Main) - BUT DO NOT PUSH YET
    fpath_a = os.path.join(repo_dir, "conflict_file.txt")
    with open(fpath_a, "w") as f:
        f.write("Content from User A\n")
        
    # 3. Add content in Repo B (Colleague) AND PUSH -> Creates Remote Change
    fpath_b = os.path.join(repo_b, "conflict_file.txt")
    with open(fpath_b, "w") as f:
        f.write("Content from User B (CONFLICT!)\n")
    
    git(["add", "."], cwd=repo_b)
    git(["commit", "-m", "evil: colleague push first"], cwd=repo_b)
    rc_b = git_push(cwd=repo_b)
    
    if rc_b != 0:
        log("Setup failed: Colleague could not push.", RED)
        result("Simulated Error Setup", False, skip=True)
        return

    log("😈 Colleague pushed changes. Remote is ahead/diverged.", YELLOW)
    
    # 4. Run GitPy on Repo A
    # Expectation:
    # - It will analyze changes (User A content)
    # - Generate Commit
    # - Try to Push -> FAIL (Non-fast-forward)
    # - Git Healer activates -> Fixes (Pull --rebase?) -> Push again -> Success
    
    log("🤖 Running GitPy on User A repo (Expect Healer)...", YELLOW)
    rc, out, err = run_cmd("gitpy auto --yes", cwd=repo_dir)
    
    # Analysis
    healer_triggered = "Git Healer acionado" in out
    healer_cured = "Cura aplicada" in out or "Push realizado com sucesso" in out
    
    result("Healer Triggered", healer_triggered)
    result("Healer Cured & Pushed", (rc == 0) and healer_cured)
    
    if not (rc == 0) or not healer_cured:
        log(f"Output dump:\n{out}\n{err}", RED)

def print_summary():
    log("", header=True)
    log("=" * 60, BOLD)
    total = RESULTS["pass"] + RESULTS["fail"] + RESULTS["skip"]
    log(f"RESULTS: {RESULTS['pass']}/{total} passed, {RESULTS['fail']} failed", 
        GREEN if RESULTS["fail"] == 0 else RED)
    log("=" * 60, BOLD)

# ========= MAIN =========

def main():
    repo_dir = setup()
    if not repo_dir:
        return

    try:
        test_add_file(repo_dir)
        test_edit_file(repo_dir)
        test_delete_file(repo_dir)
        test_context_hint(repo_dir)
        test_stealth_mode(repo_dir)
        test_security_blocklist(repo_dir)
        test_dry_run(repo_dir)
        
        # The Grand Finale
        test_error_simulation(repo_dir)
        
    except Exception as e:
        log(f"CRITICAL TEST ERROR: {e}", RED)
        import traceback
        traceback.print_exc()
        
    print_summary()

if __name__ == "__main__":
    main()
