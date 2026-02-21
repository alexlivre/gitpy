# PROJECT_LOG — Diário do Antigravity (append-only)

Este arquivo documenta o que o usuário pediu e o que o agente fez no projeto.
Ele serve para continuidade entre sessões/máquinas e para evitar alterações desnecessárias.

## Contexto do agente (importante)
- Este projeto usa Workspace Rules em `.agent/rules/`.
- Regra principal de logging: `.agent/rules/project-journal.md`.
- A regra exige que, sempre que houver mudanças em arquivos, o agente atualize este `PROJECT_LOG.md` com uma nova entrada **logo abaixo** de `## Entradas`, sem escrever nada acima deste cabeçalho fixo. [web:221]

## Regras deste log (sempre)
- Append-only: nunca apague nem reescreva entradas antigas; sempre adicione uma nova entrada.
- Não registrar segredos: tokens, chaves, senhas, dados pessoais ou credenciais.
- Registrar apenas o que realmente foi feito (sem inventar ações).
- “Pedido do usuário” deve ser 1–3 bullets (missão em 10 segundos, sem parágrafos).

## Entradas
(As entradas começam abaixo desta linha.)

### [2026-02-21 11:40] — Config: Criação do .gitignore completo

**Pedido do usuário (1–3 bullets):**
- Criar um `.gitignore` robusto para o projeto.
- Garantir que arquivos de ambiente, logs e pastas temporárias não sejam commitados.
- Preparar o repositório para o GitHub.

**O que foi feito (mudanças reais):**
- `.gitignore` — Criado na raiz com regras para Python, .env, logs e temp files.

**Como foi feito (método):**
- Análise da estrutura de diretórios para identificar arquivos de cache e logs.
- Inclusão de padrões universais de Python e SO.

**Skills usadas (somente as realmente usadas):**
- nenhuma

**Avisos / Não mexer sem necessidade:**
- `.gitpy-private` e `.gitpy-temp/` foram explicitamente ignorados por segurança.

### [2026-02-17 09:50] — Feature: Stealth Mode (.gitpy-private)

**Pedido do usuário (1–3 bullets):**
- Criar `.gitpy-private` para ocultar arquivos do Git sem usar `.gitignore` público (ex: `.meusagentesdeia/`).
- Mover arquivos para pasta temporária `.gitpy-temp` durante a execução e restaurar depois.
- Garantir segurança (auto-add no gitignore, abort on fail).

**O que foi feito (mudanças reais):**
- `cartridges/tool/tool-stealth/` — Criado novo cartucho com lógica `stash` e `restore`.
- `launcher.py` — Integrado `tool-stealth` no início e fim do ciclo `auto` (com try/finally).
- `tests/test_stealth.py` — Criados testes unitários para validar movimentação, integridade, conflitos e recovery.
- **Safety**: Implementada lógica de anti-colisão (renomeia para `.restored`) e limpeza atômica.

**Como foi feito (método):**
- Implementação de movimentação física de arquivos (shutil.move) para uma pasta oculta.
- Verificação automática de existência da pasta temp no `.gitignore` para evitar acidentes.
- Wrapper em `launcher.py` para garantir restauração mesmo se houver erro.

**Skills usadas (somente as realmente usadas):**
- nenhuma

**Avisos / Não mexer sem necessidade:**
- A pasta `.gitpy-temp` é volátil durante a execução. Se o processo for morto com SIGKILL, arquivos podem restar lá (o launcher tenta restaurar na próxima execução).

### [2026-02-17 10:25] — Docs: Atualização do README.md

**Pedido do usuário (1–3 bullets):**
- Reescrever README.md para refletir o estado atual (Stealth Mode, Zero Config).
- Remover instruções obsoletas (gitpy.cmd inexistente).
- Destacar features de segurança.

**O que foi feito (mudanças reais):**
- `README.md` — Reescrito completamente.
- Adicionada seção "Stealth Mode".
- Corrigidas instruções de instalação e uso (`pygit.cmd` / `python launcher.py`).

**Como foi feito (método):**
- Overwrite do arquivo com base no Implementation Plan aprovado.

**Skills usadas (somente as realmente usadas):**
- nenhuma

**Avisos / Não mexer sem necessidade:**
- README agora reflete a arquitetura Vibe e os novos cartuchos. Manter atualizado se novos cartuchos forem criados.

### [2026-02-17 09:10] — Deprecation: Remoção do suporte a .gitpy

**Pedido do usuário (1–3 bullets):**
- Repensar/Remover o arquivo `.gitpy` por questões de segurança.
- Evitar riscos de usuários escreverem instruções perigosas (Prompt Injection).

**O que foi feito (mudanças reais):**
- `launcher.py` — Removida leitura e carregamento do arquivo `.gitpy`.
- `cartridges/ai/ai-brain/main.py` — Removida lógica de `EXCLUDE`, `REMOVE` e injeção de prompt do projeto.
- `tests/super_test_runner.py` — Removidos testes obsoletos (`init`, `ignore --auto`).
- `README.md` — Confirmado que não havia menções para remover (grep).

**Como foi feito (método):**
- Limpeza de código fonte removendo blocos de leitura de arquivo e parsing de resposta da LLM.
- Atualização da suite de testes para ignorar funcionalidades descontinuadas.
- Validação via testes de regressão (`local_integration.py` e `test_brain.py`).

**Skills usadas (somente as realmente usadas):**
- nenhuma

**Avisos / Não mexer sem necessidade:**
- O GitPy agora é "opinionated" e seguro por padrão, sem aceitar overrides de prompt via arquivo no repositório.

### [2026-02-17 08:30] — Execução de Bateria de Testes (Baseline & Integração)

**Pedido do usuário (1–3 bullets):**
- Executar uma bateria de testes no GitPy (funcionamento, IA).
- Criar plano e executar várias validações.

**O que foi feito (mudanças reais):**
- `tests/local_integration.py` — Criado (novo script de teste end-to-end com mocks).
- `tests/test_executor.py` — Atualizado (correção de imports dinâmicos).
- `tests/test_brain.py` — Atualizado (correção de imports dinâmicos).
- `walkthrough.md` — Criado relatório final dos testes.

**Como foi feito (método):**
- Execução de testes unitários existentes (após corrigir imports quebrados).
- Criação de cenário de integração simulando o fluxo `gitpy auto --dry-run` e detecção de IA.
- Validação de saída do CLI usando `unittest` e regex simples.

**Skills usadas (somente as realmente usadas):**
- nenhuma

**Avisos / Não mexer sem necessidade:**
- Os testes agora rodam localmente sem precisar de chaves de API reais (mocks).
- `tests/super_test_runner.py` continua existindo para testes reais com remote, mas não foi alterado.

### [2026-02-17 07:15] — Higienização: Remoção de Funcionalidades Mortas

**Pedido do usuário (1–3 bullets):**
- Eliminar tudo que não é usado pelo `gitpy auto`.
- Não mexer na segurança.
- Manter `tool-ignore` integrado ao `auto`.

**O que foi feito (mudanças reais):**
- `cartridges/tool/tool-cloner/` — Removido (só manifest, nunca implementado)
- `cartridges/tool/tool-forker/` — Removido (só manifest)
- `cartridges/tool/tool-scaffolder/` — Removido (não usado pelo auto)
- `cartridges/tool/tool-config/` — Removido (wizard do init)
- `cartridges/core/git-backup/` — Removido (shadow branches nunca integrado)
- `cartridges/core/git-config/` — Removido (substituído por leitura direta)
- `cartridges/ai/ai-style/main.py` — Removida dependência do `git-config` deletado
- `cartridges/tool/tool-ignore/main.py` — Removida dependência do `git-config` deletado
- `rastro.py` — Removidos 5 comandos CLI (init, new, clone, ignore, auth), 3 imports órfãos, simplificada tela de boas-vindas
- `debug_groq.py`, `debug_runner.py`, `debug_runner_interactive.py`, `test_import.py`, `dlc.py` — Removidos (debug órfãos)
- `README.md` — Reescrito para refletir versão higienizada

**Como foi feito (método):**
- Mapeamento completo de dependências via análise de `kernel.run()` e imports diretos.
- Verificação de que nenhum cartucho removido era chamado pelo fluxo `auto`.

**Skills usadas (somente as realmente usadas):**
- nenhuma

**Avisos / Não mexer sem necessidade:**
- De 20 cartuchos, restam 14. A segurança (Muralha de Chumbo) permanece intacta.
- O `tool-ignore` agora é chamado proativamente dentro do `auto` (Smart Ignore Check).
- O instalador (Inno Setup) precisará ser rebuildado para refletir a remoção dos cartuchos.

### [2026-02-15 23:23] — Fix: Conflito onde EXCLUDE cancelava REMOVE

**Pedido do usuário (1–3 bullets):**
- A feature `REMOVE:` não funcionou porque o GitPy executava `git reset HEAD` logo em seguida (devido ao `EXCLUDE:`), desfazendo a deleção stagada.

**O que foi feito (mudanças reais):**
- `rastro.py` — Adicionado filtro para remover de `excluded_files` qualquer arquivo que esteja em `removed_files`.

**Como foi feito (método):**
- Antes de processar exclusões, fazemos `excluded_files = [f for f in excluded_files if f not in removed_files]`.
- Isso garante que se um arquivo foi marcado para remoção (`git rm`), ele não será resetado, mantendo a deleção no commit.

**Skills usadas (somente as realmente usadas):**
- nenhuma

**Pendências:**
### [2026-02-17 07:35] — Remoção do Suporte a Inno Setup/PyInstaller

**Pedido do usuário (1–3 bullets):**
- Remover arquivos de build do instalador (Inno Setup/PyInstaller).
- O projeto ainda não está maduro o suficiente para distribuição compilada.

**O que foi feito (mudanças reais):**
- `installer/` — Pasta removida (scripts `build.py` e `setup.iss`).
- `gitpy.spec` — Removido (config do PyInstaller).
- `build/`, `dist/` — Pastas de artefatos de build removidas.
- `temp_*` — Pastas temporárias de teste limpas da raiz.
- `README.md` — Removida seção de instruções de build.

**Como foi feito (método):**
- Limpeza via `Remove-Item` no PowerShell.

**Skills usadas (somente as realmente usadas):**
- nenhuma

### [2026-02-17 07:45] — Limpeza Profunda (Deep Clean)

**Pedido do usuário (1–3 bullets):**
- Analisar a pasta app e eliminar arquivos de debug, logs e artefatos não essenciais.
- Manter apenas a aplicação pura e funcional.

**O que foi feito (mudanças reais):**
- `gitpy.md` — Removido (spec antiga obsoleta, substituída pelo `README.md`).
- `pygit.cmd` — Removido (script legado).
- `gitpy_dev.cmd` — Renomeado para `gitpy.cmd` (launcher padrão).
- `*.log`, `*.txt` — Removidos 7 arquivos de log/debug (`build_log`, `debug_output`, etc).
- `tests/` — Mantida (qualidade de código).

**Como foi feito (método):**
- Análise manual de cada arquivo na raiz.
- Remoção de tudo que não era código fonte, teste ou documentação ativa.

**Skills usadas (somente as realmente usadas):**
- nenhuma

### [2026-02-17 07:55] — Renomeação para launcher.py

**Pedido do usuário (1–3 bullets):**
- Renomear `rastro.py` para `launcher.py`.
- O nome deve refletir melhor sua função de ponto de entrada.

**O que foi feito (mudanças reais):**
- `rastro.py` — Renomeado para `launcher.py`.
- `gitpy.cmd` — Atualizado para chamar `launcher.py`.
- `VIBE_ENGINEERING_GUIDE.md` — Atualizada referência ao Launcher.
- Cartridges e Testes — Atualizados todos os scripts e comentários que referenciavam `rastro.py`.

**Como foi feito (método):**
- Rename via filesystem.
- Grep e replace em massa nos arquivos dependentes.

**Skills usadas (somente as realmente usadas):**
- nenhuma

### [2026-02-17 08:00] — Reescrita da Documentação (README.md)

**Pedido do usuário (1–3 bullets):**
- Reescrever o `README.md` refletindo a nova realidade do projeto.
- Focar no comando único `gitpy auto` e no novo nome `launcher.py`.

**O que foi feito (mudanças reais):**
- `README.md` — Reescrito do zero.
- Destaques: Instalação Expressa, One Command Rule (`gitpy auto`), Flags Essenciais e Seção "Under the Hood" (Healer, Security, Vibe Arch).

**Como foi feito (método):**
- Redação focada em UX: menos comandos, mais automação.
- Explicação clara do `launcher.py` como maestro da orquestra de cartuchos.

**Skills usadas (somente as realmente usadas):**
- page-copywriter-pro (para clareza e síntese)

### [2026-02-17 08:05] — Refinamento Visual do README

**Pedido do usuário (1–3 bullets):**
- Atualizar o `README.md` (solicitação genérica após a explicação dos comandos).
- Alinhar a documentação com a resposta detalhada fornecida no chat.

**O que foi feito (mudanças reais):**
- `README.md` — Tabelas de flags reformuladas para separar "Atalho" e "Função".
- Adicionada seção explícita de "Opções Globais".

**Como foi feito (método):**
- Edição direta do markdown para melhorar legibilidade.

**Skills usadas (somente as realmente usadas):**
- nenhuma

### [2026-02-17 12:45] — Fix: Leak de .gitpy-private e Otimização do Git Healer

**Pedido do usuário (1–3 bullets):**
- Corrigir vazamento de `.gitpy-private` para o GitHub (segurança).
- Garantir que ele seja ignorado automaticamente pelo `.gitignore`.

**O que foi feito (mudanças reais):**
- `cartridges/tool/tool-ignore/main.py` — Adicionado `.gitpy-private` à lista `COMMON_TRASH` para sugestão automática.
- `cartridges/core/git-healer/main.py` — Ajustado prompt do sistema para instruir a IA a resolver conflitos de rebase (`git add` + `continue`) em vez de abortar.
- `cartridges/core/git-executor/main.py` — Injetadas variáveis de ambiente (`GIT_TERMINAL_PROMPT=0`) para evitar travamentos em processos interativos.
- `tests/true_test_suite.py` — Adicionada asserção crítica para garantir que `.gitpy-private` não seja commitado.

**Como foi feito (método):**
- Alteração na lista de constantes do `tool-ignore`.
- Prompt Engineering no `git-healer` para melhorar raciocínio sobre estados de conflito.
- Validação completa via `tests/true_test_suite.py` (15/15 testes passados, incluindo auto-cura).

**Skills usadas (somente as realmente usadas):**
- nenhuma

**Avisos / Não mexer sem necessidade:**
- O Git Healer agora é capaz de resolver conflitos de merge/rebase reais. Não reverter a lógica do prompt sem testes rigorosos.
