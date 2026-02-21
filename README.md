# GitPy: O Co-Piloto DevOps para Seus Repositórios ☁️🤖

> **"Não apenas versiona. Entende, Protege, Automatiza e Conserta."**

O **GitPy** é uma CLI de próxima geração que transforma seu fluxo de trabalho Git. Construído sobre a **Arquitetura Vibe** (sistema modular de cartuchos plugáveis) e alimentado por IA (Llama 4 via Groq, OpenAI, Gemini, Ollama), ele atua como um engenheiro DevOps sênior pareando com você em tempo real.

---

## 🌟 Destaques

| Feature | Descrição |
| :--- | :--- |
| **🧠 Cérebro de IA** | Analisa seus diffs e escreve mensagens de commit semânticas (Conventional Commits). |
| **🥷 Stealth Mode** | **NOVO!** Oculta arquivos privados (ex: agentes IA) temporariamente durante a execução, sem sujar o `.gitignore`. |
| **🚑 Git Healer** | Detecta erros de push (conflitos, rejects) e **corrige automaticamente** usando IA. |
| **🤖 Modo Automático** | `gitpy auto` assume o controle (scan → commit → push) sem perguntas. |
| **🛡️ Muralha de Chumbo** | Impede que chaves de API, senhas (`.env`) e arquivos sensíveis sejam commitados. |
| **📦 Vibe Vault** | Detecta diffs gigantes (>100KB) e os resume automaticamente para a IA funcionar. |
| **🧹 Smart Ignore** | Verifica proativamente o `.gitignore` antes de cada commit e sugere limpeza. |

---

## 🛠️ Instalação Expressa

### Pré-requisitos
- Python 3.10+
- Git instalado e configurado.

### 1. Clone & Setup
```bash
git clone https://github.com/alexlivre/gitpy.git
cd gitpy/app
pip install -r requirements.txt
```

### 2. Configure a IA (.env)
Crie um arquivo `.env` na pasta `app/` (use o `.env.example` como base):
```ini
GROQ_API_KEY=gsk_...     # Recomendado (Prioridade Máxima 🚀)
OPENAI_API_KEY=sk-...    # Opcional (Fallback)
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

O GitPy foi desenhado para ser "Zero Config". Você só precisa de um comando:

```bash
python launcher.py auto
```

O launcher iniciará o processo de automação inteligente:
1.  **Stealth Stash:** Esconde seus arquivos privados (`.gitpy-private`).
2.  **Scanner:** Verifica mudanças e sugere adições ao `.gitignore`.
3.  **Think:** Analisa o código com IA e gera o commit.
4.  **Act:** Realiza o commit e o push seguro.
5.  **Restore:** Devolve seus arquivos privados.

### Flags e Opções

| Flag | Atalho | Função |
| :--- | :--- | :--- |
| `--yes` | `-y` | **Confirmação Automática:** Aceita tudo sem perguntar. |
| `--dry-run` | | **Simulação:** Mostra o que seria feito, sem executar Git. |
| `--no-push` | | **Commit Local:** Faz o commit, mas não envia ao remoto. |
| `--message "..."` | `-m` | **Dica de Contexto:** Orienta a IA (ex: `-m "fix login"`). |
| `--model <nome>` | | **Escolher IA:** Força `groq`, `openai`, `gemini` ou `ollama`. |

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

## 🧩 O que acontece "Under the Hood"?

### 🚑 Git Healer (Auto-Correção)
Se o `git push` falhar (ex: conflito, remoto à frente), o GitPy não desiste. Ele entra em modo de cura, pede instruções à IA sobre como corrigir o erro específico, aplica a correção e tenta novamente.

### 🛡️ Muralha de Chumbo (Security)
Um sistema de 3 camadas protege seus segredos:
1.  **Blocklist:** Impede leitura de arquivos `.env` e chaves SSH.
2.  **Redactor:** Mascara senhas e tokens no diff antes de enviar para a IA.
3.  **Stealth Mode:** Esconde fisicamente arquivos sensíveis durante a operação.

### 📦 Vibe Architecture (Cartridges)
O GitPy é modular. Cada funcionalidade é um "cartucho" isolado em `cartridges/`:
-   `ai/`: Adaptadores para diferentes LLMs.
-   `core/`: Lógica Git profunda (Scanner, Executor, Healer).
-   `security/`: Módulos de proteção.
-   `tool/`: Ferramentas auxiliares (Stealth, Smart Ignore).

O arquivo `launcher.py` é apenas o maestro que rege essa orquestra.

---

**GitPy: Code Smarter, Not Harder.** 💜
