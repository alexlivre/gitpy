# Guia Técnico para API dos Modelos GPT-5 Mini e Nano

## 1. Introdução aos Modelos GPT-5 Mini e Nano

A família GPT-5 oferece modelos otimizados para diferentes cenários de uso. Os modelos **GPT-5-mini** e **GPT-5-nano** são versões compactas e eficientes, ideais para:

- **GPT-5-mini**: Raciocínio com otimização de custos e chat - equilibra velocidade, custo e capacidade
- **GPT-5-nano**: Tarefas de alta vazão, especialmente classificação simples ou seguimento de instruções básicas

Estes modelos são particularmente adequados para aplicações que exigem baixa latência, alto throughput e custos reduzidos.

## 2. Configuração Inicial da API

### Autenticação
```python
import os
from openai import OpenAI

# Configure sua chave de API
client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY")
)
```

### Instalação do SDK
```bash
pip install openai
```

## 3. Parâmetros da API - Atualização Crítica

### ⚠️ **Parâmetros Incompatíveis com Reasoning Effort**

Os parâmetros `temperature`, `top_p` e `logprobs` **só são suportados** quando o `reasoning.effort` está definido como `"none"`.

**Comportamento por modelo:**

| Modelo | Parâmetros Suportados | Observação |
|--------|----------------------|------------|
| `gpt-5.2` com `reasoning.effort="none"` | ✅ `temperature`, `top_p`, `logprobs` | Totalmente compatível |
| `gpt-5.2` com `reasoning.effort≠"none"` | ❌ `temperature`, `top_p`, `logprobs` | Causará erro |
| `gpt-5.1` com qualquer `reasoning.effort` | ❌ `temperature`, `top_p`, `logprobs` | Causará erro |
| `gpt-5`, `gpt-5-mini`, `gpt-5-nano` | ❌ `temperature`, `top_p`, `logprobs` | Causará erro |

### 🔧 **Parâmetros Alternativos Recomendados**

Para modelos que não suportam os parâmetros tradicionais, use estas alternativas:

#### 1. **Depth of Reasoning (Profundidade de Raciocínio)**
```python
response = client.responses.create(
    model="gpt-5-mini",  # ou "gpt-5-nano"
    input="Sua pergunta aqui",
    reasoning={
        "effort": "low"  # Opções: "none", "low", "medium", "high", "xhigh"
    }
)
```

#### 2. **Verbosity Control (Controle de Verbosidade)**
```python
response = client.responses.create(
    model="gpt-5-mini",
    input="Sua pergunta aqui",
    text={
        "verbosity": "medium"  # Opções: "low", "medium", "high"
    }
)
```

#### 3. **Output Length Control (Controle de Tamanho)**
```python
response = client.responses.create(
    model="gpt-5-nano",
    input="Sua pergunta aqui",
    max_output_tokens=500  # Limite máximo de tokens de saída
)
```

## 4. Exemplos Práticos de Uso

### Exemplo 1: Classificação Simples (GPT-5-nano)
```python
# Classificação de sentimento - ideal para alta vazão
response = client.responses.create(
    model="gpt-5-nano",
    input="Classifique o sentimento deste texto: 'Estou muito feliz com o produto!'",
    text={
        "verbosity": "low"
    },
    max_output_tokens=50
)

print(response.output_text)
```

### Exemplo 2: Chat Otimizado (GPT-5-mini)
```python
# Conversação com custo otimizado
response = client.responses.create(
    model="gpt-5-mini",
    input="Explique o conceito de machine learning em uma frase",
    reasoning={
        "effort": "low"
    },
    text={
        "verbosity": "medium"
    }
)

print(response.output_text)
```

### Exemplo 3: Extração de Informações Estruturadas
```python
response = client.responses.create(
    model="gpt-5-mini",
    input="Extraia nome, email e telefone do texto: 'João Silva, joao@email.com, (11) 99999-8888'",
    reasoning={
        "effort": "none"
    },
    # Para reasoning="none", podemos usar temperature
    temperature=0.1  # Baixa temperatura para respostas consistentes
)

print(response.output_text)
```

## 5. Tabela Comparativa de Configurações

| Caso de Uso | Modelo Recomendado | Reasoning Effort | Verbosity | Max Output Tokens |
|-------------|-------------------|------------------|-----------|-------------------|
| Classificação em massa | GPT-5-nano | "none" ou "low" | "low" | 100-200 |
| Chat rápido | GPT-5-mini | "low" | "medium" | 300-500 |
| Extração de dados | GPT-5-mini | "none" | "low" | 200-400 |
| Resumo conciso | GPT-5-nano | "low" | "low" | 150-250 |
| Explicações detalhadas | GPT-5-mini | "medium" | "high" | 500-1000 |

## 6. Melhores Práticas para Otimização

### Cache de Prompt
```python
# Utilize cache para prompts repetitivos
response = client.responses.create(
    model="gpt-5-nano",
    input="Classifique: {texto}",
    reasoning={"effort": "none"},
    cache_control={"type": "ephemeral"}
)
```

### Batch Processing
```python
# Processamento em lote para alta vazão
requests = [
    {"model": "gpt-5-nano", "input": f"Texto {i}", "max_output_tokens": 100}
    for i in range(100)
]

# Use threading ou async para processamento paralelo
```

### Monitoramento de Custos
```python
# Calcule custos aproximados
def estimate_cost(model, input_tokens, output_tokens):
    pricing = {
        "gpt-5-mini": {"input": 0.15, "output": 0.60},  # $ por 1M tokens
        "gpt-5-nano": {"input": 0.10, "output": 0.40},
    }
    cost = (input_tokens * pricing[model]["input"] / 1_000_000 +
            output_tokens * pricing[model]["output"] / 1_000_000)
    return cost
```

## 7. Tratamento de Erros

```python
import openai
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
def safe_api_call(model, input_text, **kwargs):
    try:
        response = client.responses.create(
            model=model,
            input=input_text,
            **kwargs
        )
        return response
    except openai.BadRequestError as e:
        if "temperature" in str(e) and model in ["gpt-5-mini", "gpt-5-nano"]:
            # Remove parâmetros incompatíveis e tenta novamente
            kwargs.pop("temperature", None)
            kwargs.pop("top_p", None)
            kwargs.pop("logprobs", None)
            return safe_api_call(model, input_text, **kwargs)
        raise e
```

## 8. Migração de Modelos Anteriores

| Modelo Antigo | Novo Modelo | Configuração Recomendada |
|---------------|-------------|--------------------------|
| `gpt-4.1-mini` | `gpt-5-mini` | `reasoning.effort="low"` + prompt tuning |
| `gpt-4.1-nano` | `gpt-5-nano` | `reasoning.effort="none"` + prompt tuning |
| `o4-mini` | `gpt-5-mini` | `reasoning.effort="medium"` |

## 9. Conclusão

Os modelos **GPT-5-mini** e **GPT-5-nano** oferecem excelente relação custo-benefício para aplicações de produção. Lembre-se:

1. **Nunca use `temperature`, `top_p`, ou `logprobs`** com `reasoning.effort` diferente de `"none"`
2. **Prefira `verbosity` e `max_output_tokens`** para controle de saída
3. **Ajuste `reasoning.effort`** conforme a complexidade da tarefa
4. **Monitore custos** cuidadosamente em aplicações de alta escala

Para cenários mais complexos que exigem raciocínio profundo, considere migrar para `gpt-5.2` com configurações apropriadas.

---

**Recursos Adicionais:**
- [Documentação Oficial GPT-5](https://platform.openai.com/docs/models/gpt-5)
- [Guia de Prompting para GPT-5](https://platform.openai.com/docs/guides/prompting/gpt-5-prompting)
- [Calculadora de Custos](https://openai.com/pricing)