# Plano de Testes GitPy (Vibe Architecture)

Este documento define a bateria de testes completa para validar a robustez, segurança e inteligência do GitPy.
Use este checklist para acompanhar a validação manual ou automatizada do sistema.

---

## 🛠️ 1. Testes de Infraestrutura (Core)
Validação dos componentes fundamentais do sistema.

- [x] **Instalação e Ambiente**
    - [x] Verificar instalação via `pip install -r requirements.txt`.
    - [x] Verificar se `gitpy.cmd` está no PATH e executável de qualquer diretório.
    - [x] Verificar carregamento do `.env` (chaves de API).

- [x] **Git Scanner (`core/git-scanner`)**
    - [/] **Cenário 1: Repositório Vazio**: Rodar em pasta sem `.git` -> Deve retornar erro tratável.
    - [x] **Cenário 2: Working Tree Clean**: Rodar em repo sem mudanças -> Deve avisar "Nada a fazer" e sair.
    - [x] **Cenário 3: Diffs Grandes**: Testar com arquivo > 100KB -> Deve ativar `smart_pack` (Vibe Vault).
    - [x] **Cenário 4: Untracked Files**: Verificar se novos arquivos são detectados corretamente.

- [x] **Git Executor (`core/git-executor`)**
    - [x] **Cenário 1: Whitelist**: Executar comandos permitidos (`status`, `add`, `commit`) -> Sucesso.
    - [x] **Cenário 2: Blacklist**: Tentar executar `git rm`, `git clean` ou flags perigosas (`--hard`) -> **Deve ser bloqueado**.
    - [ ] **Cenário 3: Dry Run**: Rodar com `--dry-run` -> Mostrar comando sem executar.

---

## 🛡️ 2. Testes de Segurança (Muralha de Chumbo)
Garantir que segredos nunca vazem.

- [x] **Sanitizer (`sec-sanitizer`) - Blocklist Imutável**
    - [x] Tentar commitar arquivo `.env` -> **Deve ser ignorado/bloqueado automaticamente**.
    - [x] Tentar commitar chave SSH (`id_rsa`) -> **Bloqueio Total**.
    - [x] Tentar commitar pasta `.vscode/` ou `.idea/` (se configurado na blocklist).

- [x] **Redactor (`sec-redactor`) - Data Masking**
    - [x] **Cenário 1: Email**: Criar arquivo com `user@empresa.com` -> Diff deve mostrar `[REDACTED:Email]`.
    - [x] **Cenário 2: API Key**: Colocar string `sk-abc123456...` -> Diff deve mostrar `[REDACTED:Generic_Token]`.
    - [x] **Cenário 3: IP Address**: Colocar IP `192.168.1.1` -> Diff deve mostrar `[REDACTED:IP_Address]`.

---

## 🧠 3. Testes de Inteligência (AI Brain)
Validação da geração de conteúdo pela IA.

- [x] **Conectividade LLM**
    - [x] Testar adaptador **Groq** (Llama 4) -> Verificar latência e resposta.
    - [x] Testar adaptador **OpenAI** (Fallback) -> Se configurado.
    
- [x] **Qualidade do Prompt**
    - [x] **Contexto**: Verificar se a IA recebe o diff correto (sanitizado).
    - [x] **Dica do Usuário**: Rodar com `--message "ajuste de layout"` -> A IA deve respeitar a dica.
    - [x] **Auto-Correção**: Se a IA gerar markdown excessivo (```), o brain deve limpar antes de entregar.

- [x] **Style Guide (`ai/ai-style`)**
    - [x] Verificar se mensagens seguem **Conventional Commits** (`feat:`, `fix:`, `docs:`).
    - [x] Verificar uso de Emojis (se ativado no perfil do time).

---

## 🎮 4. Testes de Interface (CLI)
Experiência do usuário e argumentos.

- [x] **Fluxo Interativo (Padrão)**
    - [x] Rodar `gitpy` sem args -> Deve mostrar Spinner, Painel de Diff e Prompt de Confirmação (Y/n).
    
- [x] **Fluxo Automatizado (`--yes`)**
    - [x] Rodar `gitpy --yes` -> Deve pular todas as perguntas, fazer stage, commit e push sozinho.

- [x] **Argumentos Especiais**
    - [x] `--path <dir>`: Rodar apontando para outro diretório -> Deve funcionar igual ao local.
    - [x] `--no-push`: Deve commitar mas NÃO enviar ao remote.

---

## 🔄 5. Testes End-to-End (Integração Total)

- [x] **Ciclo de Vida Completo**
    1.  `git clone` um repo de teste.
    2.  Criar um arquivo `teste.txt`.
    3.  Rodar `gitpy main --yes --message "teste e2e"`.
    4.  Verificar no GitHub se o commit apareceu.
    5.  Verificar se o autor do commit está correto.

---

**Status da Bateria:**
- Data de Criação: 2026-02-15
- Responsável: Antigravity Agent
