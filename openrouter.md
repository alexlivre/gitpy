Este é o seu guia definitivo para dominar o **OpenRouter**, uma interface unificada que permite acessar centenas de modelos de IA através de um único endpoint. Com ele, você pode gerenciar modelos, custos e recursos multimodais (como imagens) de forma centralizada.

----------

## 1. Modelos e Provedores

O OpenRouter atua como o provedor principal, permitindo o uso de diversos modelos. Atualmente, o foco está nos seguintes modelos:

-   `meta-llama/llama-4-scout`
    
-   `google/gemma-3-12b-it`
    
-   `google/gemma-3-27b-it`
    

----------

## 2. Instalação e Configuração Inicial

Para começar a usar o SDK oficial do OpenRouter (atualmente em Beta), utilize o gerenciador de pacotes de sua preferência:

Bash

```
npm install @openrouter/sdk
# ou
pnpm add @openrouter/sdk

```

### Cabeçalhos Opcionais (Ranking)

Ao configurar o cliente, você pode incluir cabeçalhos que permitem que sua aplicação apareça no ranking do OpenRouter:

-   **HTTP-Referer:** URL do seu site.
    
-   **X-Title:** Nome do seu site.
    

----------

## 3. Realizando Chamadas de Texto

Você pode interagir com a API de três formas principais:

### Via SDK do OpenRouter

TypeScript

```
import { OpenRouter } from '@openrouter/sdk';

const openRouter = new OpenRouter({
  apiKey: '<OPENROUTER_API_KEY>',
});

const completion = await openRouter.chat.send({
  model: 'meta-llama/llama-4-scout',
  messages: [{ role: 'user', content: 'Qual o sentido da vida?' }],
});
console.log(completion.choices[0].message.content); [cite: 5, 6, 7]

```

### Via Fetch API (Direto)

Útil para ambientes onde você não quer instalar dependências extras. O endpoint principal é `https://openrouter.ai/api/v1/chat/completions`.

+1

### Via SDK da OpenAI

O OpenRouter é compatível com a biblioteca da OpenAI, bastando alterar o `baseURL` para `https://openrouter.ai/api/v1`.

----------

## 4. Guia de Envio de Imagens (Multimodal)

O envio de imagens é feito através de uma estrutura de mensagens em múltiplas partes no array `content`.

+1

### Regras Importantes:

-   **Ordem:** Recomenda-se enviar o texto do prompt primeiro e depois as imagens.
    
-   **Imagens primeiro:** Se for necessário enviar a imagem antes do texto, coloque-a no prompt de sistema.
    
-   **Quantidade:** O número de imagens permitidas varia conforme o modelo e o provedor.
    
-   **Formatos Suportados:** PNG, JPEG, WEBP e GIF.
    
    +1
    

### Métodos de Envio

Existem duas formas de enviar imagens:

+1

**Método**

**Quando usar**

**Vantagem**

**URL Direta**

Imagens públicas na web

Mais eficiente, não exige codificação local.

+1

**Base64**

Arquivos locais ou privados

Necessário para arquivos que não estão na web.

+1

#### Exemplo com URL (SDK)

TypeScript

```
const result = await openRouter.chat.send({
  model: 'google/gemma-3-27b-it',
  messages: [{
    role: 'user',
    content: [
      { type: 'text', text: "O que tem nesta imagem?" },
      { type: 'image_url', imageUrl: { url: 'https://link-da-imagem.jpg' } }
    ]
  }]
}); [cite: 29, 30]

```

#### Exemplo com Base64 (Arquivos Locais)

Para arquivos locais, você deve ler o arquivo e convertê-lo para uma string Base64 com o prefixo do tipo de conteúdo:

+1

TypeScript

```
import * as fs from 'fs';

async function encodeImage(path: string) {
  const buffer = await fs.promises.readFile(path);
  const base64 = buffer.toString('base64');
  return `data:image/jpeg;base64,${base64}`; [cite: 18, 34]
}

// No envio:
imageUrl: { url: await encodeImage('foto.jpg') } [cite: 35, 36]

```

----------

> **Dica de Especialista:** Para maior eficiência em modelos que suportam múltiplas imagens, você pode enviá-las em entradas separadas dentro do mesmo array `content`.


## 5. Guia Sem SDK (Uso Direto via API/Fetch)

Para quem prefere não depender de bibliotecas externas, o OpenRouter pode ser acessado através de requisições HTTP padrão (como o `fetch` no JavaScript) para o endpoint: `https://openrouter.ai/api/v1/chat/completions`.

+4

### Configuração de Cabeçalhos (Headers)

Para qualquer requisição, você deve incluir:

+2

-   **Authorization**: `Bearer <SUA_CHAVE_API>`.
    
    +2
    
-   **Content-Type**: `application/json`.
    
    +2
    
-   **HTTP-Referer** (Opcional): URL do seu site para rankings.
    
    +2
    
-   **X-Title** (Opcional): Título do seu site para rankings.
    
    +2
    

### Exemplo: Envio de Texto e Imagem (via URL)

Ao usar o `fetch`, o corpo da requisição (`body`) deve conter o modelo e o array de mensagens:

+4

JavaScript

```
fetch("https://openrouter.ai/api/v1/chat/completions", {
  method: "POST",
  headers: {
    "Authorization": "Bearer <OPENROUTER_API_KEY>",
    "Content-Type": "application/json"
  },
  body: JSON.stringify({
    "model": "google/gemma-3-27b-it", // Exemplo de modelo do arquivo 
    "messages": [
      {
        "role": "user",
        "content": [
          {
            "type": "text",
            "text": "O que tem nesta imagem?" // Texto primeiro 
          },
          {
            "type": "image_url",
            "image_url": {
              "url": "https://link-da-imagem.jpg" // URL direta [cite: 3, 13, 15]
            }
          }
        ]
      }
    ]
  })
});

```

### Exemplo: Envio de Imagem Local (via Base64)

Para imagens que não estão publicamente acessíveis na web, você deve converter o arquivo para Base64:

+3

1.  **Codificação**: O arquivo deve ser lido e transformado em string.
    
2.  **Formato**: A URL no JSON deve seguir o padrão `data:<tipo_mime>;base64,<dados>`.
    
3.  **Implementação**:
    
    -   Leia o buffer da imagem.
        
        +1
        
    -   Converta para string Base64.
        
    -   Insira no campo `url` do objeto `image_url`.
        
        +1
        

----------

## 6. Boas Práticas e Regras de Ouro (do seu arquivo)

-   **Ordem do Conteúdo**: Sempre envie o prompt de texto **antes** das imagens dentro do array `content` para garantir que o modelo processe corretamente.
    
-   **Imagens no Sistema**: Se for estritamente necessário que a imagem apareça primeiro na estrutura, recomenda-se colocá-la no **system prompt**.
    
-   **Múltiplas Imagens**: É possível enviar várias imagens em entradas separadas no array `content`, mas o limite exato depende do modelo escolhido.
    
-   **Tipos Suportados**: A API aceita formalmente PNG, JPEG, WEBP e GIF.
    
    +1
    

Modelos Disponíveis para estes testes:

-   `meta-llama/llama-4-scout`
    
-   `google/gemma-3-12b-it`
    
-   `google/gemma-3-27b-it`
    



----------

## 6. Integração via OpenAI SDK

Uma das maiores vantagens do OpenRouter é a sua compatibilidade nativa com a biblioteca da OpenAI. Isso permite que você mude de provedor apenas alterando a configuração inicial, sem reescrever toda a lógica de mensagens do seu app.

+1

**Exemplo em TypeScript/JavaScript:**

TypeScript

```
import OpenAI from 'openai';

const openai = new OpenAI({
  baseURL: 'https://openrouter.ai/api/v1', // URL obrigatória para redirecionar 
  apiKey: '<OPENROUTER_API_KEY>',
  defaultHeaders: {
    'HTTP-Referer': '<URL_DO_SEU_SITE>', // Opcional para ranking 
    'X-Title': '<NOME_DO_APP>',           // Opcional para ranking 
  },
});

async function main() {
  const completion = await openai.chat.completions.create({
    model: 'meta-llama/llama-4-scout', // Escolha entre os modelos disponíveis [cite: 2, 49]
    messages: [{ role: 'user', content: 'Qual a utilidade do Gemma-3?' }],
  });
  console.log(completion.choices[0].message.content); [cite: 50]
}

```

----------

## 7. Atribuição de App e Rankings

O OpenRouter possui um sistema de _leaderboard_ (ranking) de modelos e aplicações. Para que seu projeto apareça nessas estatísticas e receba a devida atribuição, é necessário enviar cabeçalhos específicos.

+1

-   **`HTTP-Referer`**: Deve conter a URL pública do seu site ou projeto.
    
    +1
    
-   **`X-Title`**: O nome amigável da sua aplicação que será exibido publicamente no OpenRouter.
    
    +1
    

> **Nota:** Estes cabeçalhos são opcionais, mas altamente recomendados para desenvolvedores que desejam visibilidade na plataforma.

----------

## 8. Manipulação Avançada de Imagens

Além do envio básico, existem regras cruciais de processamento para garantir que modelos como o **Gemma-3-27b** ou **Llama-4-Scout** entendam o contexto visual corretamente.

### Múltiplas Imagens por Requisição

-   Você pode enviar várias imagens em uma única chamada.
    
-   Cada imagem deve ser uma entrada separada no array de `content`.
    
-   **Atenção:** O número máximo de imagens permitidas depende do provedor específico do modelo escolhido.
    

### Ordem e Estrutura do Prompt

-   **Texto Primeiro:** Recomenda-se fortemente enviar o prompt de texto antes das imagens no array. Isso melhora a análise do conteúdo pelo parser.
    
-   **Imagens Primeiro:** Se o seu fluxo exigir que a imagem venha antes, a recomendação é colocar as instruções de texto no **system prompt**.
    

----------

## 9. Especificações Técnicas e Formatos

Ao lidar com arquivos locais (Base64), certifique-se de seguir os padrões de MIME type aceitos pela API.

+1

**Recurso**

**Detalhe**

**Modelos Recomendados**

`meta-llama/llama-4-scout`, `google/gemma-3-12b-it`, `google/gemma-3-27b-it`

**Formatos de Imagem**

PNG, JPEG, WEBP e GIF

+1

**Método de Envio**

Multipart messages via API `/v1/chat/completions`

**Vantagem da URL**

Mais eficiente para imagens públicas (sem necessidade de encode local)

+1

**Vantagem do Base64**

Essencial para arquivos privados ou locais

+1

----------

### Resumo de Fluxo (Sem SDK)

Para finalizar, lembre-se que se você estiver usando arquivos locais no Node.js, a conversão deve gerar uma string no formato: `data:image/jpeg;base64,` seguido do código.

