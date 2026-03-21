# VIBE ENGINEERING GUIDE 

## 1. Restrições Globais (Invariantes)

1.  **Atomicidade:** O arquivo `main.py` de um cartucho **jamais deve exceder 250 linhas**.
    
2.  **Isolamento de Canais:**
    
    -   **STDOUT:** Exclusivo para JSON de saída. Proibido `print` de texto plano.
        
    -   **STDERR:** Exclusivo para Logs e Telemetria.
        
3.  **Código Líquido:** O `manifest.json` é a única verdade imutável. A implementação (`main.py`) é descartável e reescrita conforme o ambiente muda.
    
4.  **Assincronia:** Proibido bloquear o Event Loop. Use `await` para I/O. Cálculos pesados (CPU-bound) são geridos automaticamente pelo Kernel.
    

----------

## 2. Arquitetura de Diretórios

O sistema opera sob uma estrutura rígida de domínios:

Plaintext

```
/root
  ├── vibe_core.py        # KERNEL (Imutável. API de execução e memória)
  ├── [app_name].py      # LAUNCHER (CLI, API ou UI - Ponto de entrada)
  └── /cartridges
      └── /<dominio>      # ex: 'ai', 'db', 'tool', 'nexus'
          └── /<modulo>   # ex: 'ai-openai'
              ├── manifest.json     # Contrato de Interface
              ├── main.py           # Lógica de Negócio
              ├── dlc.py            # Sidecar (Infraestrutura/Smart Pack)
              └── requirements.txt  # Dependências Conceituais

```

----------

## 3. Anatomia do Cartucho

### 3.1 O Manifesto (`manifest.json`)

O contrato deve ser definido antes do código.

**Exemplo Completo:**

JSON

```json
{
  "identity": {
    "name": "ai-analyst",
    "version": "1.2.0",
    "description": "Analisa sentimentos e extrai entidades de textos."
  },
  "io_contract": {
    "input_schema": {
      "type": "object",
      "properties": {
        "text_content": { "type": "string", "description": "Texto a ser analisado" },
        "mode": { "type": "string", "enum": ["fast", "detailed"], "default": "fast" }
      },
      "required": ["text_content"]
    },
    "output_schema": {
      "type": "object",
      "properties": {
        "sentiment": { "type": "string" },
        "entities": { "type": "array" },
        "data_ref": { "type": "string", "description": "Se houver payload pesado (via VibeVault)" }
      }
    }
  },
  "error_dictionary": {
    "API_ERR": "Falha na comunicação com o provedor externo.",
    "QUOTA_EXC": "Limite de tokens ou requisições excedido.",
    "INPUT_INV": "Texto de entrada vazio ou inválido."
  }
}

```

### 3.2 O Sidecar (`dlc.py`) e Smart Packing

Todo código repetitivo de infraestrutura reside aqui. O `dlc.py` exporta nativamente a função `smart_pack` para gestão de memória.

-   **Regra dos 100KB:** Se `len(payload) > 100KB`, o dado **não** deve trafegar no STDOUT.
    
-   **Mecanismo:** O `smart_pack` decide automaticamente entre **Base64** (JSON direto) ou **Reference ID** (VibeVault).
    

**Interface do `dlc.py`:**

Python

```
# O cartucho DEVE usar esta função para qualquer saída de dados volátil (imagens, dfs)
from vibe_core import VibeVault

def smart_pack(data: bytes, threshold_kb: int = 100) -> dict:
    """
    Retorna:
    - {"mode": "direct", "payload": "base64..."} se < 100KB
    - {"mode": "ref", "data_ref": "vibe-ref-xyz..."} se > 100KB
    """
    # Lógica pré-implementada fornecida ao agente

```

### 3.3 O Músculo (`main.py`)

Deve utilizar `argparse` para CLI, `pydantic` para validação e importar `smart_pack` se houver saída de dados complexos. Use imports relativos (`from .dlc import ...`).

----------

## 4. API do Kernel (`vibe_core.py`)

O Kernel é injetado no ambiente. Os cartuchos interagem com ele através das seguintes interfaces:

**Componente**

**Método**

**Descrição**

**Execução**

`kernel.run(path, payload, timeout)`

Executa cartucho. Se Async: usa Event Loop. Se Sync: usa Processo Isolado (CPU Safety). Hot Reload automático.

**Memória**

`VibeVault.store(obj)`

Armazena objeto em RAM e retorna `ref_id`.

**Memória**

`VibeVault.retrieve(ref_id)`

Recupera objeto original.

**Memória**

`async with VibeVault.auto_cleanup(ref_id)`

Context Manager para uso seguro (Obrigatório).

**Logs**

`kernel.log(module, cid, msg, level)`

Escreve no STDERR formatado.

----------

## 5. Protocolo de Observabilidade

1.  **Correlation ID (CID):**
    
    -   Gerado pelo Kernel ou passado via payload (`payload['cid']`).
        
    -   **Obrigatório:** Todo log e todo `return` deve conter o `cid`.
        
2.  **Formato de Log (STDERR):**
    
    -   `[TIMESTAMP][LEVEL][CID][MODULE_NAME] Mensagem`
        
3.  **Tratamento de Erros:**
    
    -   Nunca retorne exceções cruas. Capture `try/except` e retorne JSON com `code` mapeado no `manifest.json`.
        

----------

## 6. Fluxo de Desenvolvimento (Workflow)

1.  **Definição:** Criar `manifest.json`.
    
2.  **Implementação:** IA gera `main.py` usando `dlc.py` para infra.
    
3.  **Teste Isolado (CLI):**
    
    python cartridges/domain/module/main.py --json '{"input": "val", "cid": "test"}'
    
4.  **Refatoração:** Se o ambiente mudar, apenas reescreva o `main.py`. Mantenha o `dlc.py` e o `manifest.json` estáveis.

----------

## 7. Versionamento e Canary Release

O Vibe Engineering proíbe rollbacks destrutivos. Use **Traffic Splitting**.

1.  **Pastas Versionadas:** Mantenha `ai-module-v1` (Estável) e `ai-module-v2` (Beta) lado a lado.
2.  **Nexus Router:** Implemente lógica no Nexus para rotear usuários específicos (ex: admins) para a `v2`.
3.  **Fallback Automático:** Se `v2` falhar, o Nexus deve capturar o erro e chamar `v1` transparentemente.
4.  **Limpeza:** Só delete a `v1` após validação total da `v2`.
