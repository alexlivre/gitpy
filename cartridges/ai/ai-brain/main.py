"""
Central module for ai-brain functionality.
"""
import os
import re
from typing import Any, Dict

from vibe_core import kernel
# Importa configuração para garantir que o ambiente esteja carregado
import env_config


_CATEGORY_MAP = {
    "x": "x",
    "feat": "x",
    "feature": "x",
    "enhancement": "x",
    "improvement": "x",
    "melhoria": "x",
    "b": "b",
    "fix": "b",
    "bugfix": "b",
    "bug": "b",
    "hotfix": "b",
    "correcao": "b",
    "correção": "b",
    "t": "t",
    "update": "t",
    "chore": "t",
    "refactor": "t",
    "atualizacao": "t",
    "atualização": "t",
}

_MAX_DIFF_CONTEXT = 12000


def _build_diff_context(diff_text: str) -> str:
    if len(diff_text) <= _MAX_DIFF_CONTEXT:
        return diff_text

    head = diff_text[:5000]
    middle_start = max((len(diff_text) // 2) - 1000, 0)
    middle_end = middle_start + 2000
    middle = diff_text[middle_start:middle_end]
    tail = diff_text[-5000:]

    return (
        f"{head}\n"
        "\n... [SNIP: middle context omitted for brevity] ...\n\n"
        f"{middle}\n"
        "\n... [SNIP: tail context follows] ...\n\n"
        f"{tail}"
    )


def _normalize_commit_message(raw_text: str, commit_lang: str) -> str:
    clean = raw_text.replace("```", "").replace("commit:", "").strip()
    lines = [line.strip() for line in clean.splitlines() if line.strip()]

    if not lines:
        fallback = "update: general changes" if "en" in commit_lang else "update: ajustes gerais"
        fallback_detail = "details unavailable" if "en" in commit_lang else "detalhes não informados"
        return f"{fallback}\n\n- t {fallback_detail}"

    title = lines[0][:50].strip()
    body_lines = lines[1:]

    normalized_body = []
    for line in body_lines:
        line = re.sub(r"^[\-*•]\s*", "", line).strip()
        if not line:
            continue

        match = re.match(r"^(x|b|t|feat|feature|enhancement|improvement|melhoria|fix|bugfix|bug|hotfix|correcao|correção|update|chore|refactor|atualizacao|atualização)\s*[:\-]?\s*(.+)$", line, flags=re.IGNORECASE)
        if match:
            marker = _CATEGORY_MAP.get(match.group(1).lower(), "t")
            content = match.group(2).strip()
        else:
            marker = "t"
            content = line

        if content:
            normalized_body.append(f"- {marker} {content}")

    if not normalized_body:
        fallback_detail = "details unavailable" if "en" in commit_lang else "detalhes não informados"
        normalized_body = [f"- t {fallback_detail}"]

    return f"{title}\n\n" + "\n".join(normalized_body)


async def process(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Cérebro Central (Brain).
    Orquestra o fluxo de geração de commit.
    """
    # 1. Extração de Dados
    diff = payload.get("diff", "")
    repo_path = payload.get("repo_path")
    provider = payload.get("provider", "openai")
    hint = payload.get("hint")  # Dica do usuário (-m)

    if not diff and not hint:
        return {"error": "NO_CONTEXT", "message": "Sem diff ou dica para trabalhar."}

    # 2. Defesa: Sanitização (Redactor)
    # Chama o cartucho via kernel (IPC simulado)
    try:
        redact_res = await kernel.run("security/sec-redactor", {"content": diff})
        safe_diff = redact_res.get("sanitized_content", "")
    except Exception as e:
        # Fallback (arriscado, mas melhor que crashar? Não, melhor avisar)
        safe_diff = diff
        # Na V2, falhar se redactor morrer.

    # 3. Contexto: Estilo (Style)
    try:
        style_res = await kernel.run("ai/ai-style", {"repo_path": repo_path})
        style_guide = style_res.get("style_instructions", "")
    except:
        style_guide = ""

    project_instructions = ""  # Deprecated

    # 4. Construção do Prompt
    commit_lang = payload.get("commit_lang", "en")
    lang_instruction = "English (en-US)" if "en" in commit_lang else "Português Brasileiro (pt-BR)"
    
    system_prompt = f"""Você é um Assistente DevOps Sênior.
Sua missão é escrever mensagens de commit Git claras, detalhadas e úteis.
{style_guide}

Regras:
- Título curto (max 50 chars).
- Sempre incluir corpo explicativo em bullet list.
- Cobrir as mudanças relevantes por tema, evitando omitir melhorias e atualizações importantes.
- Usar quantos bullets forem necessários para representar os temas principais.
- Cada bullet deve começar EXATAMENTE com um marcador de categoria:
  - x = melhoria (feature/enhancement)
  - b = correção (bugfix)
  - t = atualização técnica (update/refactor/chore)
- Formato obrigatório do corpo:
  - x <descrição objetiva>
  - b <descrição objetiva>
  - t <descrição objetiva>
- Responda APENAS a mensagem do commit.
- Idioma das mensagens: {lang_instruction}.
"""
    is_truncated = payload.get("is_truncated", False)
    if is_truncated:
        system_prompt += "\nATENÇÃO: O diff é extenso. Gere mensagem detalhada e abrangente por temas, sem usar resumo genérico."

    diff_context = _build_diff_context(safe_diff)

    user_prompt = f"""Gere um commit para as seguintes alterações:
---
{diff_context}
---
"""
    if len(safe_diff) > _MAX_DIFF_CONTEXT:
        user_prompt += "\n(Diff extenso: enviado em recortes para maximizar cobertura temática.)"

    if hint:
        user_prompt += f"\nDica do desenvolvedor: '{hint}'"

    # 5. Resolução de Modelo e Provedor (com Fallback)
    # Se 'model' não veio no payload, tenta buscar no ambiente
    target_model = payload.get("model")
    if not target_model:
        target_model = env_config.AI_MODELS.get(provider, "")
    
    # 6. Invocação do LLM com Fallback automático
    # Lista de provedores para tentar (inclui o escolhido + disponíveis como fallback)
    providers_to_try = [provider]
    
    # Se o usuário não especificou explicitamente um provedor, adiciona fallbacks
    if payload.get("allow_fallback", True):
        available_providers = [p for p, key in env_config.API_KEYS.items() if key and p != provider]
        # Ordena por prioridade: openrouter > groq > openai > gemini > ollama
        priority = ["openrouter", "groq", "openai", "gemini", "ollama"]
        available_providers.sort(key=lambda x: priority.index(x) if x in priority else 99)
        providers_to_try.extend(available_providers)
    
    last_error = None
    for attempt_provider in providers_to_try:
        adapter_name = f"ai/ai-{attempt_provider}"
        
        # Obtém modelo para o provedor de fallback
        if attempt_provider != provider:
            target_model = env_config.AI_MODELS.get(attempt_provider, "")
        
        try:
            llm_res = await kernel.run(adapter_name, {
                "prompt": user_prompt,
                "system_instruction": system_prompt,
                "model": target_model
            })
            
            if llm_res.get("error"):
                # Se for erro de autenticação/conexão, tenta próximo provedor
                error_msg = llm_res.get("message", "").lower()
                if any(err in error_msg for err in ["auth", "key", "token", "credential", "api_key", "não encontrada"]):
                    kernel.log("ai-brain", cid, f"Provedor {attempt_provider} falhou (auth), tentando fallback...", "WARN")
                    last_error = llm_res
                    continue
                # Se for erro de conteúdo, não faz fallback
                return {
                    "success": False,
                    "error": llm_res.get("error"),
                    "message": llm_res.get("message", "Falha de comunicação ou contexto reportado pelo provedor de API.")
                }
            
            # Sucesso!
            raw_text = llm_res.get("text", "").strip()
            generated_msg = _normalize_commit_message(raw_text, commit_lang)
            
            return {
                "success": True,
                "commit_message": generated_msg,
                "excluded_files": [],
                "removed_files": [],
                "provider_used": attempt_provider,
                "redacted": redact_res.get("redacted_count", 0) > 0,
                "fallback_used": attempt_provider != provider
            }
            
        except Exception as e:
            kernel.log("ai-brain", cid, f"Provedor {attempt_provider} erro: {str(e)}", "ERROR")
            last_error = e
            continue
    
    # Todos os provedores falharam
    error_msg = str(last_error) if last_error else "Todos os provedores falharam"
    return {"success": False, "error": "ALL_PROVIDERS_FAILED", "message": f"Nenhum provedor de IA disponível. Último erro: {error_msg}"}
