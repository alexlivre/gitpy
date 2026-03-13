from vibe_core import kernel
import asyncio
import os
from typing import Dict, Any

async def process(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Cérebro Central (Brain).
    Orquestra o fluxo de geração de commit.
    """
    # 1. Extração de Dados
    diff = payload.get("diff", "")
    repo_path = payload.get("repo_path")
    provider = payload.get("provider", "openai")
    hint = payload.get("hint") # Dica do usuário (-m)
    
    if not diff and not hint:
        return {"error": "NO_CONTEXT", "message": "Sem diff ou dica para trabalhar."}

    # 2. Defesa: Sanitização (Redactor)
    # Chama o cartucho via kernel (IPC simulado)
    try:
        redact_res = await kernel.run("security/sec-redactor", {"content": diff})
        safe_diff = redact_res.get("sanitized_content", "")
    except Exception as e:
        safe_diff = diff # Fallback (arriscado, mas melhor que crashar? Não, melhor avisar)
        # Na V2, falhar se redactor morrer.
        
    # 3. Contexto: Estilo (Style)
    try:
        style_res = await kernel.run("ai/ai-style", {"repo_path": repo_path})
        style_guide = style_res.get("style_instructions", "")
    except:
        style_guide = ""

    project_instructions = "" # Deprecated

    # 4. Construção do Prompt
    system_prompt = f"""Você é um Assistente DevOps Sênior.
Sua missão é escrever mensagens de commit Git claras, concisas e úteis.
{style_guide}

Regras:
- Título curto (max 50 chars).
- Corpo explicativo (se necessário).
- Responda APENAS a mensagem do commit.
- Idioma: Português Brasileiro (pt-BR).
"""
    is_truncated = payload.get("is_truncated", False)
    if is_truncated:
        system_prompt += "\nATENÇÃO: O diff foi truncado por ser muito extenso. Baseie-se no preview disponível e gere uma mensagem genérica sobre a alteração em massa."

    user_prompt = f"""Gere um commit para as seguintes alterações:
---
{safe_diff[:3000]} 
---
"""
    if len(safe_diff) > 3000:
        user_prompt += "\n(Diff truncado por limite de tokens...)"

    if hint:
        user_prompt += f"\nDica do desenvolvedor: '{hint}'"

    # 5. Resolução de Modelo (Hierarquia: Payload > Global ENV > Provider ENV)
    # Se 'model' não veio no payload (ex: via flag), tenta buscar no ambiente
    target_model = payload.get("model") 
    if not target_model:
        # Tenta modelo global ou modelo específico do provedor
        target_model = os.getenv("AI_MODEL") or os.getenv(f"{provider.upper()}_MODEL")

    # 6. Invocação do LLM (Adapter)
    adapter_name = f"ai/ai-{provider}" # ai/ai-openai, ai/ai-gemini...
    
    try:
        llm_res = await kernel.run(adapter_name, {
            "prompt": user_prompt,
            "system_instruction": system_prompt,
            "model": target_model
        })
        
        if llm_res.get("error"):
            return {
                "success": False, 
                "error": llm_res.get("error"), 
                "message": llm_res.get("message", "Falha de comunicação ou contexto reportado pelo provedor de API.")
            }
        
        raw_text = llm_res.get("text", "").strip()
        
        # Parsing de Exclusão e Remoção
        excluded_files = []
        removed_files = []
        commit_msg_lines = []
        
        for line in raw_text.splitlines():
             commit_msg_lines.append(line)
        
        generated_msg = "\n".join(commit_msg_lines).strip()
        
        # Limpeza básica pós-IA
        generated_msg = generated_msg.replace("```", "").replace("commit:", "").strip()
        
        return {
            "success": True,
            "commit_message": generated_msg,
            "excluded_files": [], # Deprecated
            "removed_files": [], # Deprecated
            "provider_used": provider,
            "redacted": redact_res.get("redacted_count", 0) > 0
        }

    except Exception as e:
        return {"success": False, "error": "LLM_FAIL", "message": str(e)}
