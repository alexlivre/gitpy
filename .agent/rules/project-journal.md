---
trigger: always_on
---

# Rule: Project Journal (sempre atualizar)

Você DEVE manter um log persistente do trabalho do agente no arquivo `PROJECT_LOG.md` na raiz do repositório.

## Regra principal (obrigatória)
Se você propuser QUALQUER alteração em arquivos do projeto (criar/editar/remover/renomear), você DEVE incluir no MESMO conjunto de mudanças uma atualização do `PROJECT_LOG.md`.

Se você NÃO propôs mudanças em arquivos (apenas explicação, análise, brainstorming), NÃO atualize o log.

## Onde e como manter
- Caminho fixo: `./PROJECT_LOG.md` (raiz do projeto).
- O log é **append-only**: nunca apague nem reescreva entradas antigas.
- O arquivo tem um **Cabeçalho Fixo** no topo. Você NUNCA deve inserir texto acima dele.
- Novas entradas devem ser inseridas **logo abaixo** da seção `## Entradas`.

## Cabeçalho Fixo (deve existir sempre no topo do PROJECT_LOG.md)
Se `PROJECT_LOG.md` não existir, crie-o já com este cabeçalho no topo (exatamente uma vez):

# PROJECT_LOG — Diário do Antigravity (append-only)

Este arquivo documenta o que o usuário pediu e o que o agente fez no projeto.
Ele serve para continuidade entre sessões/máquinas e para evitar alterações desnecessárias.

## Regras deste log (sempre)
- Append-only: nunca apague nem reescreva entradas antigas; sempre adicione uma nova entrada.
- Não registrar segredos: tokens, chaves, senhas, dados pessoais ou credenciais.
- Registrar apenas o que realmente foi feito (sem inventar ações).
- “Pedido do usuário” deve ser 1–3 bullets (missão em 10 segundos, sem parágrafos).

## Entradas
(As entradas começam abaixo desta linha.)

## Template obrigatório de cada entrada
Insira cada nova entrada logo abaixo da seção "## Entradas", seguindo este template:

### [YYYY-MM-DD HH:mm] — <título curto da tarefa>

**Pedido do usuário (1–3 bullets):**
- <1 linha>
- <1 linha>
- <1 linha>

**O que foi feito (mudanças reais):**
- `<caminho/do/arquivo>` — <1 linha>
- `<caminho/do/arquivo>` — <1 linha>

**Como foi feito (método):**
- <2–6 bullets>

**Skills usadas (somente as realmente usadas):**
- page-copywriter-pro
- seo-landing-page-specialist-ptbr
- ui-ux-landing-page-pro
- (ou “nenhuma”)

**Avisos / Não mexer sem necessidade:**
- <ex.: “Copy já foi fechada pelo page-copywriter-pro; não reescrever sem motivo e sem pedir.”>
- <ex.: “Estrutura H1/H2 otimizada pelo SEO; não quebrar hierarquia.”>
- <ex.: “CTA/contraste definidos no UI/UX; não diluir a cor de ação.”>

**Pendências / Próximos passos (opcional):**
- <1–3 bullets, se existir>

## Regras de qualidade (não negociáveis)
- Não invente ações: registre somente o que realmente aconteceu.
- Nunca registre segredos (tokens, chaves, senhas, dados sensíveis).
- Se você citar “skill usada”, ela deve ter impactado a decisão/entrega.
- Se existirem múltiplas tarefas na mesma sessão, registre só o que foi efetivamente concluído/alterado.

## Checklist obrigatório de fechamento (sempre no fim da resposta)
Ao finalizar QUALQUER resposta em que você propôs mudanças em arquivos, termine com este bloco:

Checklist:
- Arquivos alterados: <lista curta> (ou “nenhum”)
- PROJECT_LOG.md atualizado: sim/não
- Se “não”, explique por quê (ex.: “não houve mudança em arquivos”)
