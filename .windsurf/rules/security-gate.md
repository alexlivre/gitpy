---
trigger: always_on
---
# Security gate

- Antes de marcar qualquer tarefa como concluida, invoque `@appsec-pentest`.
- Nunca responda com pronto, done, finalizado ou equivalente sem executar a skill ou sem declarar bloqueio explicito.
- Se a tarefa alterar frontend, backend, autenticacao, autorizacao, API, banco, container, deploy, env, upload, integracao externa ou logs, a verificacao de seguranca e obrigatoria.
- Se houver falhas criticas ou altas nao corrigidas, o status final da tarefa deve ser BLOQUEADO.
- Se faltarem credenciais, ambiente, seed de banco ou forma de subir a aplicacao, pare e informe exatamente o bloqueio.
- Para aplicacoes web, valide navegador e HTTP/API.
- Para APIs, valide rotas, auth, authz, headers, CORS, erros e rate limiting.
- Para CLIs, valide entrada, execucao de comandos, arquivos, paths, permissoes e logs.
- Sempre gere ou atualize `SECURITY_REPORT.md` ao final da validacao.
