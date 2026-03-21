# GitPy: The DevOps Co-Pilot for Your Repositories ☁️🤖

> **"It doesn't just version. It Understands, Protects, Automates, and Heals."**

**GitPy** is a next-generation CLI that transforms your Git workflow. Built on the **Vibe Architecture** (a modular pluggable cartridge system) and powered by AI (currently via **Groq**), it acts as a senior DevOps engineer pairing with you in real-time.

---

## 🌟 Highlights

| Feature | Description |
| :--- | :--- |
| **🧠 AI Brain** | Analyzes your diffs and writes semantic commit messages (Conventional Commits). |
| **🔄 Regenerate Messages** | **NEW!** Regenerate commit messages interactively until you're satisfied. |
| **🥷 Stealth Mode** | **NEW!** Temporarily hides private files (e.g., AI agents) during execution without cluttering `.gitignore`. |
| **🚑 Git Healer** | Detects push errors (conflicts, rejects) and **automatically fixes** them using AI. |
| **🤖 Auto Mode** | `gitpy auto --yes` takes total control (scan → commit → push) without questions. |
| **🏗️ Skip Deploy** | **NEW!** Use `--nobuild` to add `[CI Skip]` and avoid automatic deployments. |
| **🛡️ Lead Wall** | Prevents API keys, passwords (`.env`), and sensitive files from being committed. |
| **📦 Vibe Vault** | Detects giant diffs (>100KB) and automatically summarizes them for the AI to process. |
| **🧹 Smart Ignore** | Proactively checks `.gitignore` before each commit and suggests cleanup. |
| **🛠️ Deep Trace** | **NEW!** Captures raw AI payloads and responses in `.vibe-debug.log` for deep debugging. |
| **⚙️ Modular Config** | **NEW!** List of ignorable files editable via `common_trash.json`. |
| **🎯 Smart Whitelist** | **NEW!** Custom exceptions via comments in `.gitignore`. |
| **🔒 .Env Security** | **NEW!** Unbreakable security lock to protect `.env`. |
| **🧪 AI Diagnostics** | **NEW!** `check-ai` command to test keys and connectivity. |
| **🚀 Multi-Provider** | **NEW!** Native support for **OpenRouter** and **OpenAI GPT-5**. |
| **🌍 Multi-Language** | **NEW!** i18n support (English/Portuguese) for both interface and commits. |
| **🌿 Test Branch Mode** | **NEW!** Create/use test branches with `--branch` flag for safe operations. |

---

## 🎮 Usage Guide: The One Command

GitPy was designed to be "Zero Config". The main command is:

```bash
python launcher.py auto
```

> **Note:** By default, GitPy will ask for confirmation before pushing. For a **fully autonomous** experience (no questions), add the `--yes` flag:
> ```bash
> python launcher.py auto --yes
> ```

The launcher will start the intelligent automation process:
1.  **Stealth Stash:** Hides your private files (`.gitpy-private`).
2.  **Scanner:** Checks for changes and suggests additions to `.gitignore`.
3.  **Think:** Analyzes the code with AI and generates the commit.
4.  **Review:** Shows you the generated commit message with options to:
    - **Execute** - Proceed with the current message
    - **Regenerate** - Ask AI for a new message (repeat as needed)
    - **Cancel** - Abort the operation
5.  **Act:** Performs the commit and secure push.
6.  **Restore:** Returns your private files to their place.

### Interactive Menu Mode (NEW!)

GitPy now supports a guided menu powered by **InquirerPy**.

```bash
# Opens the interactive menu (when terminal is interactive / TTY)
python launcher.py

# Explicit menu command
python launcher.py menu

# Optional wrappers
gitpy
gitpy menu
```

Menu coverage:
- `Auto` wizard exposes all current options: `path`, `model`, `message`, `branch`, `dry_run`, `no_push`, `nobuild`, `debug`, `yes`.
- `Branch Center` now includes branch-specific operations: current branch, list local/remote, validate name, create+switch, and switch existing branch.
- `Check AI` runs the same diagnostics flow as `python launcher.py check-ai`.
- `Reset Repository` opens `git_reset_to_github.py` in guided modes (`summary`, `dry-run`, `full reset`).
- `View Resources` shows the complete GitPy resource map (CLI flows, wrappers, global options, i18n).
- `Exit` closes the interactive session.

After each operation, you can return to the main menu and keep navigating without restarting GitPy.
Prompt behavior is now explicit: list prompts use arrows + Enter, text prompts ask you to type and press Enter.

Compatibility notes:
- Existing CLI flows are unchanged (`auto`, `check-ai`, all flags and ordering continue to work).
- In non-interactive environments (CI/pipes, no TTY), GitPy will not try to open menus automatically.
- `InquirerPy` is now part of dependencies (`pip install -r requirements.txt`).

### Usage Examples

```bash
# Full automatic mode
python launcher.py auto --yes

# Create and use a test branch for safe operations
python launcher.py auto --yes --branch feature-test

# Use existing branch
python launcher.py auto --yes --branch existing-branch

# Avoid automatic deployment (useful to save build quota)
python launcher.py auto --yes --nobuild

# Local commit only, no push
python launcher.py auto --yes --no-push

# Simulation to check what will be done
python launcher.py auto --dry-run

# Combine branch with other flags
python launcher.py auto --yes --branch test --no-push --nobuild
```

### Flags and Options

| Flag | Shortcut | Function | Usage Example |
| :--- | :--- | :--- | :--- |
| `--yes` | `-y` | **Automatic Confirmation:** Accepts everything without asking, enabling fully autonomous execution. | `gitpy auto --yes` |
| `--dry-run` | | **Simulation:** Shows what would be done without executing any Git commands. Useful to verify actions before confirming. | `gitpy auto --dry-run` |
| `--no-push` | | **Local Commit:** Performs the commit but doesn't send to remote. Ideal for work-in-progress commits or when you want to group multiple commits before pushing. | `gitpy auto --yes --no-push` |
| `--nobuild` | | **Skip Deploy:** Adds `[CI Skip]` to the message to avoid auto-deploy on CI/CD systems. Saves build quota. | `gitpy auto --yes --nobuild` |
| `--branch <name>` | `-b` | **Test Branch:** Creates or uses a specific branch for operations. If branch doesn't exist, it will be created automatically. Useful for isolated work. | `gitpy auto --yes --branch feature-test` |
| `--message "..."` | `-m` | **Context Hint:** Provides a context hint for AI to generate a more specific commit message. Ex: `-m "fix login"` directs AI to focus on login fixes. | `gitpy auto -m "fix login bug"` |
| `--model <name>` | | **Choose Provider:** Manually selects AI provider (auto, openrouter, groq, openai, gemini, ollama). Overrides `AI_PROVIDER` from `.env`. | `gitpy auto --model groq` |
| `--debug` | | **Deep Trace:** Enables advanced diagnostic mode, saving AI payloads and responses to `.vibe-debug.log`. Essential for debugging integration issues. | `gitpy --debug auto` |
| `--path <dir>` | `-p` | **Target:** Sets target directory for GitPy execution. Allows operating on repositories different from current directory. | `gitpy --path /path/to/repo auto` |

#### Practical Combined Examples:

```bash
# Full autonomous flow
gitpy auto --yes

# Local commit for work-in-progress
gitpy auto --yes --no-push

# Test changes in isolated branch without deploy
gitpy auto --yes --branch experiment --nobuild --no-push

# Simulate to see what would happen
gitpy auto --dry-run

# Commit with specific context using specific AI
gitpy auto --yes -m "refactor auth" --model openai

# Debug AI integration issues
gitpy --debug auto --model groq
```

### 🛠️ Diagnostic Commands
**NEW!** GitPy now allows you to test the health of your AI configuration:

```bash
python launcher.py check-ai
```

This command checks if your API keys are correctly configured and attempts a basic communication with all available providers, displaying an informative table.

### 🌍 Global Options
_(Use these flags before or after `auto`)_

| Flag | Shortcut | Function |
| :--- | :--- | :--- |
| `--debug` | | **Deep Trace:** Enables deep payload tracking in `.vibe-debug.log`. |
| `--path <dir>` | `-p` | **Target:** Runs GitPy in another directory. |

---

## 🔄 Message Regeneration (NEW!)

**NEW!** GitPy now allows you to regenerate commit messages interactively until you're satisfied with the result.

### How it works:
After the AI generates a commit message, GitPy presents you with three options:

1. **Execute Commit** - Proceed with the current message
2. **Generate New Message** - Ask the AI to create a different message
3. **Cancel Operation** - Abort the process

### Usage Flow:
```bash
# Run the auto command
gitpy auto

# GitPy will:
# 1. Analyze your changes
# 2. Generate initial commit message
# 3. Show you the message with options
# 4. Wait for your choice
# 5. If you choose "regenerate", repeat from step 2
# 6. If you choose "execute", perform the commit
```

### Benefits:
- **Perfect Messages**: Keep regenerating until you get the perfect commit message
- **No More Frustration**: Never get stuck with a poorly generated message
- **Iterative Process**: Multiple attempts with the same context
- **Full Control**: You decide when the message is good enough

### Compatibility:
- **With --yes**: Automatically executes without asking (preserves autonomous workflow)
- **Without --yes**: Shows the interactive menu with all three options
- **Fallback**: If InquirerPy is not available, uses simple yes/no confirmation

---

## 🌿 Test Branch Mode (--branch)

**NEW!** GitPy now supports creating and using test branches to safely test changes without affecting your main branch.

### How it works:
- When you use `--branch <name>`, GitPy will:
  1. **Create** the branch if it doesn't exist
  2. **Switch** to the specified branch
  3. **Perform** all operations (scan, commit, push) on that branch
  4. **Keep** you on the test branch after operations complete

### Usage Examples:
```bash
# Create a new test branch and work on it
python launcher.py auto --yes --branch feature-login-fix

# Use an existing branch
python launcher.py auto --yes --branch develop

# Combine with other flags for complete control
python launcher.py auto --yes --branch experiment --no-push --nobuild
```

### Benefits:
- **Safety**: Test changes without risking your main branch
- **Isolation**: Keep experimental work separate
- **Flexibility**: Works with all existing GitPy features
- **Convenience**: One command to create, switch, and work on a branch

### Branch Name Validation:
GitPy validates branch names to ensure they follow Git standards:
- Must start with a letter or number
- Can contain letters, numbers, dots, hyphens, and underscores
- Cannot be reserved names (HEAD, master, main, etc.)
- Maximum 255 characters

### 🔄 Branch Navigation with GitPy

**PRO TIP:** You can use GitPy's `--branch` flag to navigate between existing branches, not just create new ones.

#### Navigation Examples:
```bash
# Switch to main branch and work there
python launcher.py auto --yes --branch main

# Switch to development branch
python launcher.py auto --yes --branch develop

# Switch to any existing branch
python launcher.py auto --yes --branch feature-auth
```

#### How it works:
- **If branch exists**: GitPy switches to it and performs operations there
- **If branch doesn't exist**: GitPy creates it first, then switches
- **Without --branch**: GitPy works on your current branch

#### Common Workflow:
```bash
# You're currently on a test branch
$ git branch --show-current
dev-teste

# Switch back to main using GitPy
python launcher.py auto --yes --branch main

# Now you're on main and ready to work
$ git branch --show-current
main
```

This makes GitPy a complete branch management tool, not just for creating test branches!

---

## 🥷 Stealth Mode (.gitpy-private)

Need to keep sensitive files in your project folder (like agent configs, local logs) but don't want them in Git or to clutter the public `.gitignore`?

Create a `.gitpy-private` file in the project root and list your patterns (just like `.gitignore`):

```text
# .gitpy-private
.my_secret_folder/
local_logs.txt
agent_configs_x/*.json
```

**How it works:**
1. When running, GitPy moves these files to a hidden temporary folder (`.gitpy-temp`).
2. Git runs "blind", without seeing these files.
3. At the end, GitPy restores everything to its original place.
4. **Safety:** If the power goes out or an error occurs, GitPy restores them in the next run. If there's a name conflict, it saves a backup.

---

## 🏗️ Skip Deploy Mode (--nobuild)

**NEW!** Save your build quota on services like Cloudflare Pages (500/month limit) using the `--nobuild` flag.

### How it works:
- When you use `--nobuild`, GitPy automatically adds `[CI Skip]` to the beginning of the commit message.
- This signals to CI/CD services that they should skip the automatic deployment for this commit.
- The AI continues generating the commit message normally, just with the additional prefix.

### Usage Example:
```bash
# Commits and pushes normally, but avoids auto-deploy
gitpy auto --yes --nobuild

# combine with other flags
gitpy auto --yes --nobuild --no-push  # Local commit only
gitpy auto --yes --nobuild -m "fix: critical bug fix"  # With custom message
```

### Resulting Message:
If the AI generates `fix: adjusts button margin`, with `--nobuild` it becomes:
```
[CI Skip] fix: adjusts button margin
```

---

## ⚙️ Modular Configuration (common_trash.json)

**NEW!** GitPy now allows full customization of the list of files and folders considered "trash" to be ignored.

### How it works:
- The pattern list is in `cartridges/tool/tool-ignore/common_trash.json`.
- You can edit this file to add, remove, or modify patterns.
- GitPy dynamically loads this list without needing to touch the Python code.

### common_trash.json Example:
```json
[
    ".env",
    "__pycache__/",
    "*.pyc",
    "*.log",
    ".DS_Store",
    "node_modules/",
    "build/",
    ".vscode/",
    ".idea/",
    "coverage/",
    "*.swp",
    ".gitpy-private"
]
```

### Security:
- If the JSON file doesn't exist or is corrupted, GitPy uses a safe default list.
- The default list always includes: `[".env", "node_modules/", "build/"]`.

---

## 🎯 Smart Whitelist (.gitignore)

**NEW!** Total control over what should or should not be suggested as "trash" using special comments in your `.gitignore`.

### How to use:
Add a comment in the format:
```gitignore
# ["item1", "item2"] do not ignore
```

### Practical examples:
```gitignore
# ["build", "node_modules"] do not ignore
*.log
*.pyc
.DS_Store

# ["coverage"] do not ignore
.env
```

### Result:
- `build/` and `node_modules/` WILL NOT be suggested as "trash" to ignore.
- `coverage/` WILL NOT be suggested as "trash" to ignore.
- Whitelist items always take priority over `common_trash.json`.

### Use cases:
- **Production Build**: When you want to intentionally commit the `build/` folder.
- **Specific Node_modules**: When you need certain dependencies in the repository.
- **Config Folders**: When you need to version files that would normally be ignored.

---

## 🔒 .Env Security (Panic Lock)

**NEW!** GitPy implements an unbreakable security barrier to protect your `.env` files and passwords.

### How it works:
If you try to add `.env` to the whitelist (exceptions), GitPy:

1. **STOPS IMMEDIATELY** all automatic operations.
2. **Displays a high-impact visual alert:**
   ```
   ⚠️ SECURITY ALERT: The .env file has been marked as NOT to be ignored. 
   This could expose your passwords on GitHub!
   ```
3. **Returns a security error** that prevents proceeding.
4. **Requires manual confirmation** from the user.

### Example that triggers the alert:
```gitignore
# [".env"] do not ignore
```

### Why this is important:
- **Protection against accidents**: Prevents passwords and API keys from being committed by mistake.
- **Unbreakable security**: Not even `--yes` or auto mode overrides this alert.
- **Security awareness**: Forces the user to think twice before exposing sensitive data.

### If you really need to commit .env:
1. Remove the exception comment from `.gitignore`.
2. Manually add `.env` to the standard `.gitignore`.
3. **Think very carefully** if it's truly necessary to expose this information.

---

## 🌍 Internationalization (Multi-Language)

**NEW!** GitPy is now global. You can configure different languages for the software interface and for the messages that the AI writes in the commits.

### Config in .env:
- `LANGUAGE`: Defines the language for CLI messages, help menus, and logs. (Options: `en`, `pt`).
- `COMMIT_LANGUAGE`: Defines in which language the AI should write its commit messages. (e.g., `en`, `pt-br`, `es`).

### Bilingual Example:
If you want the interface in Portuguese but work in an international repository where commits should be in English:
```env
LANGUAGE=pt
COMMIT_LANGUAGE=en
```

### Safe Fallback:
If a translation is missing or the language file is not found, GitPy automatically uses **English** as fallback, ensuring the application never breaks due to a missing translation.

## 🛠️ Modo Debug Profundo (Deep Trace)

**NOVO!** O GitPy agora inclui um sistema de rastreamento de baixo nível para diagnosticar falhas silenciosas na IA ou problemas de integração.

### Como funciona:
Quando ativado pela flag `--debug`, o Kernel do GitPy intercepta toda comunicação entre os cartuchos.

1.  **Payload In:** Captura exatamente o que foi enviado para a IA (prompt, diff, parâmetros).
2.  **Result Out:** Captura a resposta bruta retornada, incluindo códigos de erro técnicos que normalmente seriam omitidos na interface simplificada.
3.  **Log de Vibe:** Tudo é gravado em formato JSON no arquivo `.vibe-debug.log` na raiz do projeto.

### Exemplo de uso para diagnóstico:
```bash
# Se o commit falhar sem mensagem clara, rode com debug:
python launcher.py --debug auto
```

### Por que usar?
- **Erros de IA:** Descubra se o Groq/OpenAI está retornando erros de cota, modelo inexistente ou filtros de segurança.
- **Auditoria:** Veja exatamente o que está sendo enviado para as LLMs para garantir privacidade.
- **Desenvolvimento:** Facilita a criação de novos cartuchos monitorando o fluxo de dados.

---

## 📋 Exemplos Práticos: Configuração e Segurança

### Exemplo 1: Build em Produção
Você quer commitar a pasta `build/` intencionalmente para deploy:

**1. Edite seu .gitignore:**
```gitignore
# ["build"] do not ignore
*.log
node_modules/
.env
```

**2. Execute o GitPy normalmente:**
```bash
gitpy auto --yes
```

**Resultado:** O GitPy NÃO sugerirá adicionar `build/` ao .gitignore, permitindo que você versione sua pasta de build.

---

### Exemplo 2: Node_modules Específicos
Você precisa versionar `node_modules` para um projeto crítico:

**1. Configure a whitelist:**
```gitignore
# ["node_modules"] do not ignore
*.log
.env
build/
```

**2. Personalize o common_trash.json (opcional):**
```json
[
    ".env",
    "*.log",
    "build/",
    "coverage/",
    "dist/"
]
```

---

### Exemplo 3: Proteção .Env (Segurança)
Cenário perigoso - alguém tenta remover .env da proteção:

**1. .gitignore perigoso:**
```gitignore
# [".env"] do not ignore
*.log
node_modules/
```

**2. Resultado imediato:**
```
⚠️ ALERTA DE SEGURANÇA: O arquivo .env foi marcado para NÃO ser ignorado. 
Isso pode expor suas senhas no GitHub!
ERRO: Operação cancelada por segurança.
```

**3. O GitPy PARA completamente até que o risco seja removido.**

---

### Exemplo 4: Workflow Completo
Configure um projeto com controle total:

**1. common_trash.json personalizado:**
```json
[
    ".env",
    "*.log",
    "*.tmp",
    "cache/",
    "temp/",
    "vendor/",
    "coverage/",
    ".DS_Store"
]
```

**2. .gitignore com exceções:**
```gitignore
# ["vendor", "cache"] do not ignore
*.log
.env
temp/
coverage/
```

**3. Execute com segurança:**
```bash
gitpy auto --yes --nobuild  # Evita deploy automático
```

**Resultado:**
- ✅ `vendor/` e `cache/` não serão sugeridos como lixo
- ✅ `*.log`, `.env`, `temp/`, `coverage/` serão sugeridos normalmente
- ✅ Deploy automático será evitado

---

## 🧩 What happens "Under the Hood"?

### ⚙️ Modular Configuration System
GitPy now has an intelligent configuration system that balances **flexibility** and **security**:

1. **Dynamic Loading**: The "trash" list is loaded from `common_trash.json` with a safe fallback.
2. **Exception Parser**: Analyzes comments in `.gitignore` in the format `# ["item1"] do not ignore`.
3. **Priority Whitelist**: Exceptions in `.gitignore` always win over the default list.
4. **.Env Security Lock**: Automatic detection of `.env` in exceptions with a total block.

### 🚑 Git Healer (Auto-Correction)
If `git push` fails (e.g., conflict, remote ahead), GitPy doesn't give up. It enters healer mode, asks the AI for instructions on how to fix the specific error, applies the fix, and tries again.

### 🛡️ Lead Wall (Security)
A 3-layer system protects your secrets:
1.  **Blocklist:** Prevents reading of `.env` files and SSH keys.
2.  **Redactor:** Masks passwords and tokens in the diff before sending to the AI.
3.  **Stealth Mode:** Physically hides sensitive files during the operation.
4.  **Panic Lock .Env:** Visual alert and total block if `.env` is marked as an exception.

### 📦 Vibe Architecture (Cartridges)
GitPy is modular. Each functionality is an isolated "cartridge" in `cartridges/`:
-   `ai/`: Adapders for different LLMs.
-   `core/`: Deep Git logic (Scanner, Executor, Healer).
-   `security/`: Protection modules.
-   `tool/`: Auxiliary tools (Stealth, Smart Ignore, Tool-Ignore with modular configuration).

The `launcher.py` file is just the conductor leading this orchestra.

---

**GitPy: Code Smarter, Not Harder.** 💜

## 🧰 GitPy Command Line Wrappers

### gitpy.cmd
- Runs `python "%~dp0launcher.py" %*` using the same directory as the [`launcher.py`](file:///c:/code/GitHub/gitpy/launcher.py) file so that GitPy can be invoked from any folder. The `%~dp0` expands to the folder where the `.cmd` resides, ensuring that all relative imports and project assets are resolved even when the command is called outside the root.
- Since it directly invokes the Python available in the system PATH, it avoids the need to type the full path to `launcher.py` or change directories before running the automation.

### pygit.cmd
- Activates the project's virtual environment by calling `C:\code\GitHub\gitpy\.venv\Scripts\activate.bat`, allowing subsequent commands (like `python launcher.py auto`) to reuse the project's fixed dependencies without manually reconfiguring anything.
- By maintaining the absolute path to `.venv`, the wrapper eliminates the need to locate the virtual environment on each machine and facilitates its use in any Windows terminal.

### Why these wrappers exist and how to adapt the paths
Wrappers solve two main pain points on Windows:
1. **Relative path resolution**: `%~dp0` ensures Python locates `launcher.py` and associated modules even when you are in another folder.
2. **Consistent virtualenv**: `pygit.cmd` connects you directly to the `.venv` located at the repository root, ensuring the same set of dependencies used by the team.

Both use absolute paths (`C:\code\GitHub\gitpy\` and `C:\code\GitHub\gitpy\.venv\Scripts\activate.bat`) as examples only. To adapt the wrappers in another environment:
- **Windows**: find the real repository path (explorer or `cd`). In `pygit.cmd`, replace the prefix with the correct directory (`YOUR_PATH\.venv\Scripts\activate.bat`). Keep `gitpy.cmd` with `%~dp0` to continue resolving the launcher automatically. When moving the folder, just update the system PATH to include the new root.
- **Linux/macOS**: create `gitpy.sh` and `pygit.sh` scripts in the root with `SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"` and use `source "$SCRIPT_DIR/.venv/bin/activate"`. Add the root directory to the PATH via `~/.profile`, `~/.bashrc`, or equivalent.

### Adding the GitPy folder to Windows PATH
1. Open the Start menu and search for "Edit the system environment variables".
2. Under "System variables", select `Path` and click "Edit".
3. Add a new item with the full path of the folder containing `gitpy.cmd` and `pygit.cmd`.
4. Confirm and open a new terminal to load the updated PATH.
5. (Optional) run `refreshenv` or restart the terminal.

### Success Verification on Windows
- `where gitpy.cmd` should return the full path to the script.
- `gitpy auto --dry-run` should work from any folder without needing `cd`.
- `pygit` should show the `(.venv)` prefix and allow `pygit python launcher.py --help`.

### Porting logic to Linux: gitpy.sh and pygit.sh
- **Structure**:
  ```bash
  #!/usr/bin/env bash
  SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  python "$SCRIPT_DIR/launcher.py" "$@"
  ```
- **Activating virtualenv**:
  ```bash
  #!/usr/bin/env bash
  SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  source "$SCRIPT_DIR/.venv/bin/activate"
  ```
- **Differences and permissions**:
  1. `.cmd` depends on Windows commands (`@echo off`, `%~dp0`); `.sh` requires shebang, `$(...)` and `"$@"` for arguments.
  2. `.sh` needs `chmod +x gitpy.sh pygit.sh`; `.cmd` works without extra permission.
  3. Use `/usr/local/bin` or `~/.local/bin` for global versions or create `ln -s /path/to/gitpy.sh /usr/local/bin/gitpy`.

### How to verify virtual environment activation
- **Windows (cmd/powershell)**:
  1. Run `C:\your\path\gitpy\pygit.cmd` and confirm the `(.venv)` prefix.
  2. `where python` should point to `.venv\Scripts\python.exe`.
  3. `python -c "import os; print(os.environ.get('VIRTUAL_ENV'))"` should print the virtualenv path.
- **Linux/macOS**:
  1. `source /your/path/gitpy/.venv/bin/activate` should show the `(.venv)` prefix.
  2. `which python` should point to `.venv/bin/python`.
  3. `echo $VIRTUAL_ENV` and `python -c "import sys; print(sys.prefix)"` should match the `.venv`.

### Replacing examples in wrappers
- On Windows, update `pygit.cmd` to `D:\workspace\gitpy\.venv\Scripts\activate.bat` or use `%~dp0` for relative paths.
- On Linux, confirm `pwd` and adjust `source "$SCRIPT_DIR/.venv/bin/activate"` to point to the correct `.venv`.

### Usage examples after setup
- **Windows**:
  ```powershell
  cd C:\Users\alice\projects\other-repo
  gitpy auto --yes --no-push
  pygit python launcher.py --dry-run
  ```
- **Linux** (assuming `/usr/local/bin` in PATH):
  ```bash
  cd ~/other-project
  gitpy auto --yes --nobuild
  pygit python launcher.py --help
  ```
These commands work from any directory because the PATH resolves the wrappers globally and each script discovers the GitPy root internally.

### Final observations
Keep the wrappers in the project root and use the commands described above as templates. Update the paths whenever you move the repository or recreate the `.venv`, ensuring consistency for the entire team.
