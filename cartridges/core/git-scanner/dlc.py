from vibe_core import VibeVault


def smart_pack_diff(diff_content: str, max_chars: int = 4000) -> dict:
    """
    Empacota o diff de forma inteligente.

    1. Se pequeno (< max_chars): Retorna direto.
    2. Se grande: Armazena no VibeVault e retorna referência.
    """
    if not diff_content:
        return {"content": "", "mode": "direct"}

    size = len(diff_content)

    if size <= max_chars:
        return {
            "content": diff_content,
            "mode": "direct",
            "size": size
        }
    else:
        # Armazena na memória compartilhada (VibeVault)
        ref_id = VibeVault.store(diff_content)
        return {
            "data_ref": ref_id,
            "mode": "ref",
            "size": size,
            # Preview para debug
            "preview": diff_content[:500] + "\n... [TRUNCATED] ..."
        }
