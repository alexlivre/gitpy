# GitPy: O Co-Piloto DevOps para Seus Repositórios ☁️🤖

> **"Ele não apenas versiona. Ele Entende, Protege, Automatiza e Cura."**

**GitPy** é uma CLI de última geração que transforma seu fluxo de trabalho Git. Construído na **Vibe Architecture** (um sistema modular de cartuchos plugáveis) e alimentado por IA (atualmente via **Groq**), ele age como um engenheiro DevOps sênior trabalhando com você em tempo real.

---

## 🌟 Destaques

| Funcionalidade | Descrição |
| :--- | :--- |
| **🧠 Cérebro IA** | Analisa seus diffs e escreve mensagens de commit semânticas (Conventional Commits). |
| **🥷 Stealth Mode** | **NOVO!** Oculta temporariamente arquivos privados (ex: agentes IA) durante execução sem poluir `.gitignore`. |
| **🚑 Git Healer** | Detecta erros de push (conflitos, rejeições) e **corrige automaticamente** usando IA. |
| **🤖 Modo Auto** | `gitpy auto --yes` assume controle total (scan → commit → push) sem perguntas. |
| **🏗️ Skip Deploy** | **NOVO!** Use `--nobuild` para adicionar `[CI Skip]` e evitar deployments automáticos. |
| **🛡️ Muralha de Chumbo** | Impede que chaves de API, senhas (`.env`) e arquivos sensíveis sejam commitados. |
| **📦 Vibe Vault** | Detecta diffs gigantes (>100KB) e resume automaticamente para a IA processar. |
| **🧹 Smart Ignore** | Verifica proativamente `.gitignore` antes de cada commit e sugere limpeza. |
| **🛠️ Deep Trace** | **NOVO!** Captura payloads e respostas brutas da IA em `.vibe-debug.log` para debug profundo. |
| **⚙️ Config Modular** | **NOVO!** Lista de arquivos ignoráveis editável via `common_trash.json`. |
| **🎯 Smart Whitelist** | **NOVO!** Exceções personalizadas via comentários no `.gitignore`. |
| **🔒 .Env Security** | **NOVO!** Bloqueio de segurança inquebrável para proteger `.env`. |
| **🧪 AI Diagnostics** | **NOVO!** Comando `check-ai` para testar chaves e conectividade. |
| **🚀 Multi-Provider** | **NOVO!** Suporte nativo para **OpenRouter** e **OpenAI GPT-5**. |
| **🌍 Multi-Language** | **NOVO!** Suporte i18n (Inglês/Português) para interface e commits. |
| **🌿 Modo Branch de Teste** | **NOVO!** Crie/use branches de teste com flag `--branch` para operações seguras. |

---

## 🎮 Guia de Uso: O Único Comando

GitPy foi projetado para ser "Zero Config". O comando principal é:

```bash
python launcher.py auto
```

> **Nota:** Por padrão, GitPy pedirá confirmação antes de fazer push. Para uma experiência **totalmente autônoma** (sem perguntas), adicione a flag `--yes`:
> ```bash
> python launcher.py auto --yes
> ```

O launcher iniciará o processo de automação inteligente:
1.  **Stealth Stash:** Oculta seus arquivos privados (`.gitpy-private`).
2.  **Scanner:** Verifica mudanças e sugere adições ao `.gitignore`.
3.  **Think:** Analisa o código com IA e gera o commit.
4.  **Act:** Realiza o commit e push seguro.
5.  **Restore:** Retorna seus arquivos privados ao lugar.

### Modo Menu Interativo (NOVO!)

Agora o GitPy também suporta menus guiados com **InquirerPy**.

```bash
# Abre o menu interativo (quando o terminal for interativo / TTY)
python launcher.py

# Comando explícito de menu
python launcher.py menu

# Wrappers opcionais
gitpy
gitpy menu
```

Cobertura do menu:
- O wizard de `Auto` expõe todas as opções atuais: `path`, `model`, `message`, `branch`, `wip`, `dry_run`, `no_push`, `nobuild`, `debug`, `yes`.
- A `Central de Branches` inclui operações específicas: branch atual, listar locais/remotas, validar nome, criar+trocar e trocar para branch existente.
- `Check AI` executa o mesmo diagnóstico de `python launcher.py check-ai`.
- `Resetar Repositório` abre o `git_reset_to_github.py` em modos guiados (`summary`, `dry-run`, `reset completo`).
- `Ver Recursos` mostra o mapa completo dos recursos do GitPy (fluxos CLI, wrappers, opções globais, i18n).
- `Sair` fecha a sessão interativa.

Após cada operação, você pode voltar ao menu principal e continuar navegando sem reiniciar o GitPy.
Comportamento dos prompts agora está explícito: listas usam setas + Enter, campos de texto pedem digitação + Enter.

Notas de compatibilidade:
- Os fluxos CLI existentes continuam iguais (`auto`, `check-ai`, todas as flags e ordem de uso).
- Em ambiente não interativo (CI/pipes, sem TTY), o GitPy não tenta abrir menus automaticamente.
- `InquirerPy` agora faz parte das dependências (`pip install -r requirements.txt`).

### Exemplos de Uso

```bash
# Modo totalmente automático
python launcher.py auto --yes

# Crie e use uma branch de teste para operações seguras
python launcher.py auto --yes --branch feature-test

# Use branch existente
python launcher.py auto --yes --branch branch-existente

# Evite deployment automático (útil para economizar cota de build)
python launcher.py auto --yes --nobuild

# Commit local apenas, sem push
python launcher.py auto --yes --no-push

# Simulação para verificar o que será feito
python launcher.py auto --dry-run

# Combine branch com outras flags
python launcher.py auto --yes --branch test --no-push --nobuild
```

### Flags e Opções

| Flag | Atalho | Função |
| :--- | :--- | :--- |
| `--yes` | `-y` | **Confirmação Automática:** Aceita tudo sem perguntar. |
| `--dry-run` | | **Simulação:** Mostra o que seria feito, sem executar Git. |
| `--no-push` | | **Commit Local:** Realiza o commit mas não envia ao remoto. |
| `--nobuild` | | **Skip Deploy:** Adiciona `[CI Skip]` à mensagem para evitar auto-deploy. **NOVO!** |
| `--branch <nome>` | `-b` | **Branch de Teste:** Cria/usar branch de teste para operações. **NOVO!** |
| `--message "..."` | `-m` | **Dica de Contexto:** Guia a IA (ex: `-m "fix login"`). |
| `--model <nome>` | | **Escolher Provider:** Seleciona a IA (openrouter, groq, openai, gemini, ollama). Sobrescreve `AI_PROVIDER` do `.env`. |

### 🛠️ Comandos de Diagnóstico
**NOVO!** GitPy agora permite testar a saúde da sua configuração de IA:

```bash
python launcher.py check-ai
```

Este comando verifica se suas chaves de API estão configuradas corretamente e tenta uma comunicação básica com todos os providers disponíveis, exibindo uma tabela informativa.

### 🌍 Opções Globais
_(Use estas flags antes ou depois de `auto`)_

| Flag | Atalho | Função |
| :--- | :--- | :--- |
| `--debug` | | **Deep Trace:** Ativa rastreamento profundo de payloads em `.vibe-debug.log`. |
| `--path <dir>` | `-p` | **Alvo:** Executa GitPy em outro diretório. |

---

## 🌿 Modo Branch de Teste (--branch)

**NOVO!** GitPy agora suporta criar e usar branches de teste para testar alterações com segurança sem afetar sua branch principal.

### Como funciona:
- Quando você usa `--branch <nome>`, GitPy irá:
  1. **Criar** a branch se não existir
  2. **Alternar** para a branch especificada
  3. **Realizar** todas as operações (scan, commit, push) naquela branch
  4. **Manter** você na branch de teste após completar as operações

### Exemplos de Uso:
```bash
# Crie uma nova branch de teste e trabalhe nela
python launcher.py auto --yes --branch feature-login-fix

# Use uma branch existente
python launcher.py auto --yes --branch develop

# Combine com outras flags para controle completo
python launcher.py auto --yes --branch experiment --no-push --nobuild
```

### Benefícios:
- **Segurança:** Teste alterações sem arriscar sua branch principal
- **Isolamento:** Mantenha trabalho experimental separado
- **Flexibilidade:** Funciona com todas as funcionalidades existentes do GitPy
- **Conveniência:** Um comando para criar, alternar e trabalhar em uma branch

### Validação de Nome de Branch:
GitPy valida nomes de branch para garantir que seguem padrões Git:
- Deve começar com letra ou número
- Pode conter letras, números, pontos, hífens e underscores
- Não pode ser nomes reservados (HEAD, master, main, etc.)
- Máximo 255 caracteres

### 🔄 Navegação entre Branches com GitPy

**DICÃO PROFISSIONAL:** Você pode usar a flag `--branch` do GitPy não apenas para criar novas branches, mas também para navegar entre branches existentes.

#### Exemplos de Navegação:
```bash
# Altere para a branch main e trabalhe lá
python launcher.py auto --yes --branch main

# Altere para a branch de desenvolvimento
python launcher.py auto --yes --branch develop

# Altere para qualquer branch existente
python launcher.py auto --yes --branch feature-auth
```

#### Como funciona:
- **Se a branch existe**: GitPy alterna para ela e realiza operações lá
- **Se a branch não existe**: GitPy cria primeiro, depois alterna
- **Sem --branch**: GitPy trabalha na sua branch atual

#### Workflow Comum:
```bash
# Você está atualmente em uma branch de teste
$ git branch --show-current
dev-teste

# Volte para a main usando GitPy
python launcher.py auto --yes --branch main

# Agora você está na main e pronto para trabalhar
$ git branch --show-current
main
```

Isso transforma o GitPy em uma ferramenta completa de gerenciamento de branches, não apenas para criar branches de teste!

---

## 🥷 Stealth Mode (.gitpy-private)

Precisa manter arquivos sensíveis na pasta do seu projeto (como configs de agentes, logs locais) mas não quer它们 no Git ou poluir o `.gitignore` público?

Crie um arquivo `.gitpy-private` na raiz do projeto e liste seus padrões (assim como `.gitignore`):

```text
# .gitpy-private
.my_secret_folder/
local_logs.txt
agent_configs_x/*.json
```

**Como funciona:**
1. Ao executar, GitPy move estes arquivos para uma pasta temporária oculta (`.gitpy-temp`).
2. Git executa "cego", sem ver estes arquivos.
3. No final, GitPy restaura tudo ao seu lugar original.
4. **Segurança:** Se faltar energia ou ocorrer erro, GitPy os restaura na próxima execução. Se houver conflito de nome, salva um backup.

---

## 🏗️ Modo Skip Deploy (--nobuild)

**NOVO!** Economize sua cota de build em serviços como Cloudflare Pages (limite de 500/mês) usando a flag `--nobuild`.

### Como funciona:
- Quando você usa `--nobuild`, GitPy adiciona automaticamente `[CI Skip]` no início da mensagem de commit.
- Isso sinaliza para serviços CI/CD que devem pular o deployment automático para este commit.
- A IA continua gerando a mensagem de commit normalmente, apenas com o prefixo adicional.

### Exemplo de Uso:
```bash
# Commits e push normalmente, mas evita auto-deploy
gitpy auto --yes --nobuild

# combine com outras flags
gitpy auto --yes --nobuild --no-push  # Commit local apenas
gitpy auto --yes --nobuild -m "fix: correção de bug crítica"  # Com mensagem personalizada
```

### Mensagem Resultante:
Se a IA gera `fix: ajusta margem do botão`, com `--nobuild` se torna:
```
[CI Skip] fix: ajusta margem do botão
```

---

## ⚙️ Configuração Modular (common_trash.json)

**NOVO!** GitPy agora permite personalização completa da lista de arquivos e pastas considerados "lixo" para serem ignorados.

### Como funciona:
- A lista de padrões está em `cartridges/tool/tool-ignore/common_trash.json`.
- Você pode editar este arquivo para adicionar, remover ou modificar padrões.
- GitPy carrega esta lista dinamicamente sem precisar tocar no código Python.

### Exemplo de common_trash.json:
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

### Segurança:
- Se o arquivo JSON não existir ou estiver corrompido, GitPy usa uma lista padrão segura.
- A lista padrão sempre inclui: `[".env", "node_modules/", "build/"]`.

---

## 🎯 Smart Whitelist (.gitignore)

**NOVO!** Controle total sobre o que deve ou não ser sugerido como "lixo" usando comentários especiais no seu `.gitignore`.

### Como usar:
Adicione um comentário no formato:
```gitignore
# ["item1", "item2"] do not ignore
```

### Exemplos práticos:
```gitignore
# ["build", "node_modules"] do not ignore
*.log
*.pyc
.DS_Store

# ["coverage"] do not ignore
.env
```

### Resultado:
- `build/` e `node_modules/` NÃO serão sugeridos como "lixo" para ignorar.
- `coverage/` NÃO será sugerido como "lixo" para ignorar.
- Itens da whitelist sempre têm prioridade sobre `common_trash.json`.

### Casos de uso:
- **Build de Produção**: Quando você quer commitar intencionalmente a pasta `build/`.
- **Node_modules Específicos**: Quando você precisa de certas dependências no repositório.
- **Pastas de Config**: Quando você precisa versionar arquivos que normalmente seriam ignorados.

---

## 🔒 .Env Security (Panic Lock)

**NOVO!** GitPy implementa uma barreira de segurança inquebrável para proteger seus arquivos `.env` e senhas.

### Como funciona:
Se você tentar adicionar `.env` à whitelist (exceções), GitPy:

1. **PARA IMEDIATAMENTE** todas as operações automáticas.
2. **Exibe um alerta visual de alto impacto:**
   ```
   ⚠️ ALERTA DE SEGURANÇA: O arquivo .env foi marcado para NÃO ser ignorado. 
   Isso pode expor suas senhas no GitHub!
   ```
3. **Retorna um erro de segurança** que impede prosseguir.
4. **Requer confirmação manual** do usuário.

### Exemplo que dispara o alerta:
```gitignore
# [".env"] do not ignore
```

### Por que isso é importante:
- **Proteção contra acidentes**: Impede que senhas e chaves de API sejam commitadas por engano.
- **Segurança inquebrável**: Nem mesmo `--yes` ou modo auto sobrepõem este alerta.
- **Consciência de segurança**: Força o usuário a pensar duas vezes antes de expor dados sensíveis.

### Se você realmente precisa commitar .env:
1. Remova o comentário de exceção do `.gitignore`.
2. Adicione manualmente `.env` ao `.gitignore` padrão.
3. **Pense muito cuidadosamente** se é realmente necessário expor esta informação.

---

## 🌍 Internacionalização (Multi-Language)

**NOVO!** GitPy agora é global. Você pode configurar diferentes idiomas para a interface do software e para as mensagens que a IA escreve nos commits.

### Config no .env:
- `LANGUAGE`: Define o idioma para mensagens CLI, menus de ajuda e logs. (Opções: `en`, `pt`).
- `COMMIT_LANGUAGE`: Define em qual idioma a IA deve escrever suas mensagens de commit. (ex: `en`, `pt-br`, `es`).

### Exemplo Bilíngue:
Se você quer a interface em português mas trabalha em um repositório internacional onde commits devem ser em inglês:
```env
LANGUAGE=pt
COMMIT_LANGUAGE=en
```

### Fallback Seguro:
Se uma tradução estiver faltando ou o arquivo de idioma não for encontrado, GitPy usa automaticamente **Inglês** como fallback, garantindo que a aplicação nunca quebre devido a tradução ausente.

## 🛠️ Modo Debug Profundo (Deep Trace)

**NOVO!** GitPy agora inclui um sistema de rastreamento de baixo nível para diagnosticar falhas silenciosas na IA ou problemas de integração.

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

## 🧩 O que acontece "Por Baixo dos Panos"?

### ⚙️ Sistema de Configuração Modular
GitPy agora tem um sistema de configuração inteligente que equilibra **flexibilidade** e **segurança**:

1. **Carregamento Dinâmico**: A lista "lixo" é carregada de `common_trash.json` com fallback seguro.
2. **Parser de Exceções**: Analisa comentários em `.gitignore` no formato `# ["item1"] do not ignore`.
3. **Whitelist de Prioridade**: Exceções em `.gitignore` sempre ganham da lista padrão.
4. **Bloqueio de Segurança .Env**: Detecção automática de `.env` em exceções com bloqueio total.

### 🚑 Git Healer (Auto-Correção)
Se `git push` falhar (ex: conflito, remoto à frente), GitPy não desiste. Ele entra no modo healer, pede à IA instruções sobre como corrigir o erro específico, aplica a correção e tenta novamente.

### 🛡️ Muralha de Chumbo (Segurança)
Um sistema de 3 camadas protege seus segredos:
1.  **Blocklist:** Impede leitura de arquivos `.env` e chaves SSH.
2.  **Redactor:** Mascaras senhas e tokens no diff antes de enviar para a IA.
3.  **Stealth Mode:** Oculta fisicamente arquivos sensíveis durante a operação.
4.  **Panic Lock .Env:** Alerta visual e bloqueio total se `.env` for marcado como exceção.

### 📦 Vibe Architecture (Cartuchos)
GitPy é modular. Cada funcionalidade é um "cartucho" isolado em `cartridges/`:
-   `ai/`: Adaptadores para diferentes LLMs.
-   `core/`: Lógica Git profunda (Scanner, Executor, Healer).
-   `security/`: Módulos de proteção.
-   `tool/`: Ferramentas auxiliares (Stealth, Smart Ignore, Tool-Ignore com configuração modular).

O arquivo `launcher.py` é apenas o maestro regendo esta orquestra.

---

**GitPy: Code Mais Inteligente, Não Mais Difícil.** 💜

## 🧰 Wrappers de Linha de Comando GitPy

### gitpy.cmd
- Executa `python "%~dp0launcher.py" %*` usando o mesmo diretório do arquivo [`launcher.py`](file:///c:/code/GitHub/gitpy/launcher.py) para que GitPy possa ser invocado de qualquer pasta. O `%~dp0` expande para a pasta onde o `.cmd` reside, garantindo que todos os imports relativos e assets do projeto sejam resolvidos mesmo quando o comando é chamado fora da raiz.
- Como invoca diretamente o Python disponível no PATH do sistema, evita a necessidade de digitar o caminho completo para `launcher.py` ou mudar de diretórios antes de executar a automação.

### pygit.cmd
- Ativa o ambiente virtual do projeto chamando `C:\code\GitHub\gitpy\.venv\Scripts\activate.bat`, permitindo que comandos subsequentes (como `python launcher.py auto`) reusem as dependências fixas do projeto sem reconfigurar manualmente nada.
- Mantendo o caminho absoluto para `.venv`, o wrapper elimina a necessidade de localizar o ambiente virtual em cada máquina e facilita seu uso em qualquer terminal Windows.

### Por que estes wrappers existem e como adaptar os caminhos
Wrappers resolvem dois pontos principais de dor no Windows:
1. **Resolução de caminho relativo**: `%~dp0` garante que Python localize `launcher.py` e módulos associados mesmo quando você está em outra pasta.
2. **Virtualenv consistente**: `pygit.cmd` conecta você diretamente ao `.venv` localizado na raiz do repositório, garantindo o mesmo conjunto de dependências usado pela equipe.

Ambos usam caminhos absolutos (`C:\code\GitHub\gitpy\` e `C:\code\GitHub\gitpy\.venv\Scripts\activate.bat`) como exemplos apenas. Para adaptar os wrappers em outro ambiente:
- **Windows**: encontre o caminho real do repositório (explorer ou `cd`). Em `pygit.cmd`, substitua o prefixo com o diretório correto (`SEU_PATH\.venv\Scripts\activate.bat`). Mantenha `gitpy.cmd` com `%~dp0` para continuar resolvendo o launcher automaticamente. Ao mover a pasta, apenas atualize o PATH do sistema para incluir a nova raiz.
- **Linux/macOS**: crie scripts `gitpy.sh` e `pygit.sh` na raiz com `SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"` e use `source "$SCRIPT_DIR/.venv/bin/activate"`. Adicione o diretório raiz ao PATH via `~/.profile`, `~/.bashrc`, ou equivalente.

### Adicionando a pasta GitPy ao Windows PATH
1. Abra o menu Iniciar e procure por "Editar as variáveis de ambiente do sistema".
2. Em "Variáveis do sistema", selecione `Path` e clique em "Editar".
3. Adicione um novo item com o caminho completo da pasta contendo `gitpy.cmd` e `pygit.cmd`.
4. Confirme e abra um novo terminal para carregar o PATH atualizado.
5. (Opcional) execute `refreshenv` ou reinicie o terminal.

### Verificação de Sucesso no Windows
- `where gitpy.cmd` deve retornar o caminho completo do script.
- `gitpy auto --dry-run` deve funcionar de qualquer pasta sem precisar de `cd`.
- `pygit` deve mostrar o prefixo `(.venv)` e permitir `pygit python launcher.py --help`.

### Portando lógica para Linux: gitpy.sh e pygit.sh
- **Estrutura**:
  ```bash
  #!/usr/bin/env bash
  SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  python "$SCRIPT_DIR/launcher.py" "$@"
  ```
- **Ativando virtualenv**:
  ```bash
  #!/usr/bin/env bash
  SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  source "$SCRIPT_DIR/.venv/bin/activate"
  ```
- **Diferenças e permissões**:
  1. `.cmd` depende de comandos Windows (`@echo off`, `%~dp0`); `.sh` requer shebang, `$(...)` e `"$@"` para argumentos.
  2. `.sh` precisa de `chmod +x gitpy.sh pygit.sh`; `.cmd` funciona sem permissão extra.
  3. Use `/usr/local/bin` ou `~/.local/bin` para versões globais ou crie `ln -s /path/to/gitpy.sh /usr/local/bin/gitpy`.

### Como verificar ativação do ambiente virtual
- **Windows (cmd/powershell)**:
  1. Execute `C:\seu\path\gitpy\pygit.cmd` e confirme o prefixo `(.venv)`.
  2. `where python` deve apontar para `.venv\Scripts\python.exe`.
  3. `python -c "import os; print(os.environ.get('VIRTUAL_ENV'))"` deve imprimir o caminho do virtualenv.
- **Linux/macOS**:
  1. `source /seu/path/gitpy/.venv/bin/activate` deve mostrar o prefixo `(.venv)`.
  2. `which python` deve apontar para `.venv/bin/python`.
  3. `echo $VIRTUAL_ENV` e `python -c "import sys; print(sys.prefix)"` devem corresponder ao `.venv`.

### Substituindo exemplos nos wrappers
- No Windows, atualize `pygit.cmd` para `D:\workspace\gitpy\.venv\Scripts\activate.bat` ou use `%~dp0` para caminhos relativos.
- No Linux, confirme `pwd` e ajuste `source "$SCRIPT_DIR/.venv/bin/activate"` para apontar para o `.venv` correto.

### Exemplos de uso após configuração
- **Windows**:
  ```powershell
  cd C:\Users\alice\projects\other-repo
  gitpy auto --yes --no-push
  pygit python launcher.py --dry-run
  ```
- **Linux** (assumindo `/usr/local/bin` no PATH):
  ```bash
  cd ~/other-project
  gitpy auto --yes --nobuild
  pygit python launcher.py --help
  ```
Estes comandos funcionam de qualquer diretório porque o PATH resolve os wrappers globalmente e cada script descobre a raiz do GitPy internamente.

### Observações finais
Mantenha os wrappers na raiz do projeto e use os comandos descritos acima como modelos. Atualize os caminhos sempre que mover o repositório ou recriar o `.venv`, garantindo consistência para toda a equipe.
