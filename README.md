# GitPy: O Co-Piloto DevOps para Seus Repositórios ☁️🤖

> **"Não apenas versiona. Entende, Protege, Automatiza e Conserta."**

O **GitPy** é uma CLI de próxima geração que transforma seu fluxo de trabalho Git. Construído sobre a **Arquitetura Vibe** (sistema modular de cartuchos plugáveis) e alimentado por IA (atualmente via **Groq**), ele atua como um engenheiro DevOps sênior pareando com você em tempo real.

---

## 🌟 Destaques

| Feature | Descrição |
| :--- | :--- |
| **🧠 Cérebro de IA** | Analisa seus diffs e escreve mensagens de commit semânticas (Conventional Commits). |
| **🥷 Stealth Mode** | **NOVO!** Oculta arquivos privados (ex: agentes IA) temporariamente durante a execução, sem sujar o `.gitignore`. |
| **🚑 Git Healer** | Detecta erros de push (conflitos, rejects) e **corrige automaticamente** usando IA. |
| **🤖 Modo Automático** | `gitpy auto --yes` assume o controle total (scan → commit → push) sem perguntas. |
| **🏗️ Skip Deploy** | **NOVO!** Use `--nobuild` para adicionar `[CI Skip]` e evitar deploys automáticos. |
| **🛡️ Muralha de Chumbo** | Impede que chaves de API, senhas (`.env`) e arquivos sensíveis sejam commitados. |
| **📦 Vibe Vault** | Detecta diffs gigantes (>100KB) e os resume automaticamente para a IA funcionar. |
| **🧹 Smart Ignore** | Verifica proativamente o `.gitignore` antes de cada commit e sugere limpeza. |
| **⚙️ Configuração Modular** | **NOVO!** Lista de arquivos ignoráveis editável via `common_trash.json`. |
| **🎯 Whitelist Inteligente** | **NOVO!** Exceções personalizadas via comentários no `.gitignore`. |
| **🔒 Segurança .Env** | **NOVO!** Trava de segurança intransponível para proteger `.env`. |

---

## 🛠️ Instalação Expressa

### Pré-requisitos
- Python 3.10+
- Git instalado e configurado.
- **Autenticação SSH**: Nos testes deste projeto, o acesso ao GitHub foi configurado utilizando pares de chaves pública/privada SSH (recomendado para maior segurança e compatibilidade com automações).

### 1. Clone & Setup
```bash
git clone https://github.com/alexlivre/gitpy.git
cd gitpy/app
pip install -r requirements.txt
```

### 2. Configure a IA (.env)
Atualmente, o GitPy requer uma chave de API do **Groq**. Outros provedores (OpenAI, Gemini, Ollama) ainda não foram implementados e serão adicionados em versões futuras.

1. Obtenha sua chave gratuita em: **[https://console.groq.com/keys](https://console.groq.com/keys)**
2. Crie um arquivo `.env` na pasta raiz do projeto (use o `.env.example` como base):

```ini
GROQ_API_KEY=gsk_...     # OBRIGATÓRIO (Único provedor suportado atualmente)
# OPENAI_API_KEY=...     # Em breve
```

### 3. Rodando o GitPy
Você pode rodar diretamente via Python ou usar o script de conveniência `pygit.cmd` (se disponível no Windows):

```bash
# Método Padrão
python launcher.py auto

# Método Curto (se pygit.cmd estiver no PATH)
pygit auto
```

---

## 🎮 Guia de Uso: The One Command

O GitPy foi desenhado para ser "Zero Config". O comando principal é:

```bash
python launcher.py auto
```

> **Nota:** Por padrão, o GitPy pedirá confirmação antes de realizar o push. Para uma experiência **totalmente autônoma** (sem perguntas), adicione a flag `--yes`:
> ```bash
> python launcher.py auto --yes
> ```

O launcher iniciará o processo de automação inteligente:
1.  **Stealth Stash:** Esconde seus arquivos privados (`.gitpy-private`).
2.  **Scanner:** Verifica mudanças e sugere adições ao `.gitignore`.
3.  **Think:** Analisa o código com IA e gera o commit.
4.  **Act:** Realiza o commit e o push seguro.
5.  **Restore:** Devolve seus arquivos privados.

### Exemplos de Uso

```bash
# Modo automático completo
python launcher.py auto --yes

# Evitar deploy automático (útil para economizar cota de builds)
python launcher.py auto --yes --nobuild

# Apenas commit local, sem push
python launcher.py auto --yes --no-push

# Simulação para verificar o que será feito
python launcher.py auto --dry-run
```

### Flags e Opções

| Flag | Atalho | Função |
| :--- | :--- | :--- |
| `--yes` | `-y` | **Confirmação Automática:** Aceita tudo sem perguntar. |
| `--dry-run` | | **Simulação:** Mostra o que seria feito, sem executar Git. |
| `--no-push` | | **Commit Local:** Faz o commit, mas não envia ao remoto. |
| `--nobuild` | | **Skip Deploy:** Adiciona `[CI Skip]` à mensagem para evitar deploy automático. **NOVO!** |
| `--message "..."` | `-m` | **Dica de Contexto:** Orienta a IA (ex: `-m "fix login"`). |
| `--model <nome>` | | **Escolher IA:** Atualmente suporta apenas `groq`. Outros (openai, gemini, ollama) em breve. |

### 🌍 Opções Globais
_(Use estas flags antes ou depois do `auto`)_

| Flag | Atalho | Função |
| :--- | :--- | :--- |
| `--debug` | | **Verbose:** Exibe logs técnicos detalhados. |
| `--path <dir>` | `-p` | **Alvo:** Roda o GitPy em outro diretório. |

---

## 🥷 Stealth Mode (.gitpy-private)

Precisa manter arquivos sensíveis na pasta do projeto (como configurações de agentes, logs locais) mas não quer que eles apareçam no Git e nem quer sujar o `.gitignore` público?

Crie um arquivo `.gitpy-private` na raiz do projeto e liste os padrões (igual ao `.gitignore`):

```text
# .gitpy-private
.minha_pasta_secreta/
meus_logs_locais.txt
configs_agente_x/*.json
```

**Como funciona:**
1. Ao rodar, o GitPy move esses arquivos para uma pasta temporária oculta (`.gitpy-temp`).
2. O Git roda "cego", sem ver esses arquivos.
3. Ao final, o GitPy restaura tudo para o lugar original.
4. **Segurança:** Se acabar a luz ou der erro, o GitPy restaura na próxima execução. Se houver conflito de nomes, ele salva backup.

---

## 🏗️ Skip Deploy Mode (--nobuild)

**NOVO!** Economize sua cota de builds em serviços como Cloudflare Pages (limite de 500/mês) usando a flag `--nobuild`.

### Como funciona:
- Quando você usa `--nobuild`, o GitPy automaticamente adiciona `[CI Skip]` ao início da mensagem de commit
- Isso sinaliza para serviços de CI/CD que eles devem pular o deploy automático deste commit
- A IA continua gerando a mensagem de commit normalmente, apenas com o prefixo adicional

### Exemplo de uso:
```bash
# Faz commit e push normalmente, mas evita deploy automático
gitpy auto --yes --nobuild

# Combine com outras flags
gitpy auto --yes --nobuild --no-push  # Commit local apenas
gitpy auto --yes --nobuild -m "fix: corrige bug crítico"  # Com mensagem customizada
```

### Mensagem resultante:
Se a IA gerar `fix: ajusta margem do botão`, com `--nobuild` vira:
```
[CI Skip] fix: ajusta margem do botão
```

---

## ⚙️ Configuração Modular (common_trash.json)

**NOVO!** O GitPy agora permite personalizar completamente a lista de arquivos e pastas que são considerados "lixo" para serem ignorados.

### Como funciona:
- A lista de padrões está em `cartridges/tool/tool-ignore/common_trash.json`
- Você pode editar este arquivo para adicionar, remover ou modificar padrões
- O GitPy carrega dinamicamente esta lista, sem precisar mexer no código Python

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
- Se o arquivo JSON não existir ou estiver corrompido, o GitPy usa uma lista padrão de segurança
- A lista padrão sempre inclui: `[".env", "node_modules/", "build/"]`

---

## 🎯 Whitelist Inteligente (.gitignore)

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
- `build/` e `node_modules/` NÃO serão sugeridos como "lixo" para ignorar
- `coverage/` NÃO será sugerido como "lixo" para ignorar
- Os itens da whitelist sempre têm prioridade sobre o `common_trash.json`

### Use cases:
- **Build em produção**: Quando você quer commitar a pasta `build/` intencionalmente
- **Node_modules específicos**: Quando precisa de certas dependências no repositório
- **Pastas de configuração**: Quando precisa versionar arquivos que normalmente seriam ignorados

---

## 🔒 Segurança .Env (Trava de Pânico)

**NOVO!** O GitPy implementa uma barreira de segurança intransponível para proteger seus arquivos `.env` e senhas.

### Como funciona:
Se você tentar adicionar `.env` à whitelist (exceções), o GitPy:

1. **PARA IMEDIATAMENTE** todas as operações automáticas
2. **Exibe um alerta visual impactante:**
   ```
   ⚠️ ALERTA DE SEGURANÇA: O arquivo .env foi marcado para NÃO ser ignorado. 
   Isso pode expor suas senhas no GitHub!
   ```
3. **Retorna um erro de segurança** que impede o prosseguimento
4. **Exige confirmação manual** do usuário

### Exemplo que dispara o alerta:
```gitignore
# [".env"] do not ignore
```

### Por que isso é importante:
- **Proteção contra acidentes**: Evita que senhas e chaves de API sejam commitadas por engano
- **Segurança intransponível**: Nem mesmo `--yes` ou modo automático ignoram este alerta
- **Consciência de segurança**: Força o usuário a pensar duas vezes antes de expor dados sensíveis

### Se você realmente precisa commitar .env:
1. Remova o comentário de exceção do `.gitignore`
2. Adicione `.env` manualmente ao `.gitignore` padrão
3. **Pense muito bem** se é realmente necessário expor essas informações

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

## 🧩 O que acontece "Under the Hood"?

### ⚙️ Sistema de Configuração Modular
O GitPy agora possui um sistema inteligente de configuração que equilibra **flexibilidade** e **segurança**:

1. **Carregamento Dinâmico**: A lista de "lixo" é carregada de `common_trash.json` com fallback seguro
2. **Parser de Exceções**: Analisa comentários no `.gitignore` no formato `# ["item1"] do not ignore`
3. **Whitelist com Prioridade**: Exceções no `.gitignore` sempre vencem sobre a lista padrão
4. **Trava de Segurança .Env**: Detecção automática de `.env` nas exceções com bloqueio total

### 🚑 Git Healer (Auto-Correção)
Se o `git push` falhar (ex: conflito, remoto à frente), o GitPy não desiste. Ele entra em modo de cura, pede instruções à IA sobre como corrigir o erro específico, aplica a correção e tenta novamente.

### 🛡️ Muralha de Chumbo (Security)
Um sistema de 3 camadas protege seus segredos:
1.  **Blocklist:** Impede leitura de arquivos `.env` e chaves SSH.
2.  **Redactor:** Mascara senhas e tokens no diff antes de enviar para a IA.
3.  **Stealth Mode:** Esconde fisicamente arquivos sensíveis durante a operação.
4.  **Trava de Pânico .Env:** Alerta visual e bloqueio total se `.env` for marcado como exceção

### 📦 Vibe Architecture (Cartridges)
O GitPy é modular. Cada funcionalidade é um "cartucho" isolado em `cartridges/`:
-   `ai/`: Adaptadores para diferentes LLMs.
-   `core/`: Lógica Git profunda (Scanner, Executor, Healer).
-   `security/`: Módulos de proteção.
-   `tool/`: Ferramentas auxiliares (Stealth, Smart Ignore, Tool-Ignore com configuração modular).

O arquivo `launcher.py` é apenas o maestro que rege essa orquestra.

---

**GitPy: Code Smarter, Not Harder.** 💜

## 🧰 Wrappers de Linha de Comando do GitPy

### gitpy.cmd
- Executa `python "%~dp0launcher.py" %*` usando o mesmo diretório do arquivo [`launcher.py`](file:///c:/code/GitHub/gitpy/launcher.py) para que o GitPy possa ser invocado de qualquer pasta. O `%~dp0` expande para a pasta onde o `.cmd` reside, garantindo que todas as importações relativas e assets do projeto sejam resolvidos mesmo quando o comando for chamado fora da raiz.
- Como invoca diretamente o Python disponível no PATH do sistema, evita a necessidade de digitar o caminho completo até o `launcher.py` ou trocar de diretório antes de executar a automação.

### pygit.cmd
- Ativa o ambiente virtual do projeto chamando `C:\code\GitHub\gitpy\.venv\Scripts\activate.bat`, permitindo que comandos subsequentes (como `python launcher.py auto`) reutilizem as dependências fixas do projeto sem reconfigurar nada manualmente.
- Ao manter o caminho absoluto para `.venv`, o wrapper elimina a necessidade de localizar o ambiente virtual em cada máquina e facilita o uso do mesmo em qualquer terminal do Windows.

### Por que esses wrappers existem e como adaptar os caminhos
Os wrappers resolvem duas dores principais no Windows:
1. **Resolução de caminho relativo**: o `%~dp0` garante que o Python localize `launcher.py` e os módulos associados mesmo quando você está em outra pasta.
2. **Virtualenv consistente**: `pygit.cmd` conecta você diretamente ao `.venv` localizado na raiz do repositório, garantindo o mesmo conjunto de dependências usado pela equipe.

Ambos usam caminhos absolutos (`C:\code\GitHub\gitpy\` e `C:\code\GitHub\gitpy\.venv\Scripts\activate.bat`) apenas como exemplo. Para adaptar os wrappers em outro ambiente:
- **Windows**: descubra o caminho real do repositório (explorador ou `cd` + `cd` + `cd` + `cd`). No `pygit.cmd`, substitua o prefixo pelo diretório correto (`SEU_CAMINHO\.venv\Scripts\activate.bat`). Mantenha `gitpy.cmd` com `%~dp0` para continuar resolvendo o launcher automaticamente. Ao mover a pasta, basta atualizar o PATH do sistema para incluir a nova raiz.
- **Linux/macOS**: crie scripts `gitpy.sh` e `pygit.sh` na raiz com `SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"` e use `source "$SCRIPT_DIR/.venv/bin/activate"`. Adicione o diretório da raiz ao PATH via `~/.profile`, `~/.bashrc` ou equivalente.

### Adicionando a pasta do GitPy ao PATH do Windows
1. Abra o menu Iniciar e pesquise por "Editar variáveis de ambiente do sistema".
2. Em "Variáveis do sistema", selecione `Path` e clique em "Editar".
3. Adicione um novo item com o caminho completo da pasta que contém `gitpy.cmd` e `pygit.cmd`.
4. Confirme e abra um novo terminal para carregar o PATH atualizado.
5. (Opcional) execute `refreshenv` ou reinicie o terminal.

### Verificação de sucesso no Windows
- `where gitpy.cmd` deve retornar o caminho completo até o script.
- `gitpy auto --dry-run` deve funcionar de qualquer pasta sem precisar de `cd`.
- `pygit` deve mostrar o prefixo `(.venv)` e permitir `pygit python launcher.py --help`.

### Portando a lógica para Linux: gitpy.sh e pygit.sh
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
  1. `.cmd` depende de comandos do Windows (`@echo off`, `%~dp0`); `.sh` requer shebang, `$(...)` e `"$@"` para argumentos.
  2. `.sh` precisa de `chmod +x gitpy.sh pygit.sh`; `.cmd` funciona sem permissão extra.
  3. Use `/usr/local/bin` ou `~/.local/bin` para versões globais ou crie `ln -s /caminho/para/gitpy.sh /usr/local/bin/gitpy`.

### Como verificar a ativação do ambiente virtual
- **Windows (cmd/powershell)**:
  1. Execute `C:\seu\caminho\gitpy\pygit.cmd` e confirme o prefixo `(.venv)`.
  2. `where python` deve apontar para `.venv\Scripts\python.exe`.
  3. `python -c "import os; print(os.environ.get('VIRTUAL_ENV'))"` deve imprimir o caminho da virtualenv.
- **Linux/macOS**:
  1. `source /seu/caminho/gitpy/.venv/bin/activate` deve mostrar o prefixo `(.venv)`.
  2. `which python` deve apontar para `.venv/bin/python`.
  3. `echo $VIRTUAL_ENV` e `python -c "import sys; print(sys.prefix)"` devem coincidir com o `.venv`.

### Substituindo os exemplos nos wrappers
- No Windows, atualize `pygit.cmd` para `D:\workspace\gitpy\.venv\Scripts\activate.bat` ou use `%~dp0` para caminhos relativos.
- No Linux, confirme o `pwd` e ajuste `source "$SCRIPT_DIR/.venv/bin/activate"` para apontar para o `.venv` correto.

### Exemplos de uso após a configuração
- **Windows**:
  ```powershell
  cd C:\Users\alice\projetos\outro-repo
  gitpy auto --yes --no-push
  pygit python launcher.py --dry-run
  ```
- **Linux** (supondo `/usr/local/bin` no PATH):
  ```bash
  cd ~/outro-projeto
  gitpy auto --yes --nobuild
  pygit python launcher.py --help
  ```
Esses comandos funcionam a partir de qualquer diretório porque o PATH resolve os wrappers globalmente e cada script descobre a raiz do GitPy internamente.

### Observações finais
Mantenha os wrappers na raiz do projeto e use os comandos descritos acima como templates. Atualize os caminhos sempre que mover o repositório ou recriar o `.venv`, garantindo consistência para toda a equipe.
