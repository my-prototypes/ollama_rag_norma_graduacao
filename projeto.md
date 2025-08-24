# Projeto Ollama RAG Local

## Arquivo run.sh

O script run.sh automatiza o setup e execução de um pipeline de RAG (Retrieval-Augmented Generation) usando Ollama e Python. Aqui está o passo a passo:

1. **Inicia o serviço Ollama:**  
   Verifica se o processo `ollama` está rodando. Se não estiver, inicia o serviço em background.

2. **Baixa os modelos necessários:**  
   Usa `ollama pull` para baixar dois modelos:  
   - `llama3.2:3b` (modelo de linguagem)  
   - `nomic-embed-text` (modelo de embeddings)

3. **Prepara o ambiente Python:**  
   Cria um ambiente virtual (`.venv`), ativa ele e instala as dependências do requirements.txt.

4. **Ingestão de PDFs:**  
   Se houver arquivos PDF na pasta pdfs, executa o script `ingest_pdfs.py` para processá-los e armazená-los na coleção `docs`.  
   Se não houver PDFs, exibe uma mensagem informando.

5. **Inicia o chat RAG:**  
   Executa o script `chat_rag.py` usando a coleção `docs`, o modelo de linguagem e o modelo de embeddings especificados.

Esse script facilita o setup do ambiente e o fluxo de trabalho para quem deseja rodar um sistema de RAG localmente.

## Arquivo ingest_pdfs.py

O script ingest_pdfs.py faz a ingestão de arquivos PDF para uma base vetorial (ChromaDB) usando embeddings gerados via Ollama. Aqui está o resumo dos principais passos:

### 1. **Configuração e Importações**
- Carrega variáveis de ambiente.
- Importa bibliotecas para leitura de PDF, requisições HTTP, manipulação de arquivos, e ChromaDB.

### 2. **Função `pdf_to_text_chunks`**
- Lê o texto de cada página do PDF.
- Junta todo o texto e divide em "chunks" (trechos) de tamanho definido (`chunk_size`), com sobreposição (`chunk_overlap`).
- Retorna uma lista de tuplas: `(chunk_text, chunk_index)`.

### 3. **Função `embed_texts`**
- Para cada trecho de texto, faz uma requisição à API `/api/embeddings` do Ollama para gerar o embedding.
- Retorna uma lista de vetores de embedding.

### 4. **Função `main`**
- Lê argumentos da linha de comando (diretório dos PDFs, nome da coleção, modelo de embedding, etc).
- Inicializa o cliente ChromaDB (persistente).
- Para cada PDF encontrado:
  - Extrai os chunks de texto.
  - Gera os embeddings dos chunks em lotes de 8.
  - Adiciona os chunks, embeddings, IDs e metadados à coleção no ChromaDB.
- Exibe mensagens de progresso e conclusão.

O script automatiza a extração de texto de PDFs, gera embeddings para cada trecho usando Ollama, e armazena tudo em uma base vetorial ChromaDB, pronta para buscas semânticas ou RAG.

## Arquivo chat_rag.py

O chat_rag.py implementa um chat RAG (Retrieval-Augmented Generation) usando Ollama e ChromaDB. Veja o fluxo principal:

### 1. **Configuração**
- Carrega variáveis de ambiente.
- Define prompts e templates para orientar o modelo a responder em português e citar fontes.

### 2. **Funções principais**
- **ollama_chat:**  
  Envia mensagens para o modelo de chat do Ollama via API e retorna a resposta.

- **embed_text:**  
  Gera o embedding de uma consulta usando o modelo de embedding do Ollama.

- **retrieve:**  
  Busca os trechos mais relevantes na coleção do ChromaDB usando o embedding da consulta. Retorna os textos, metadados (fonte e índice) e score de similaridade.

- **build_context:**  
  Monta o contexto para o modelo de linguagem, juntando os trechos recuperados e suas fontes.

### 3. **chat_loop**
- Interface de linha de comando: recebe perguntas do usuário.
- Para cada pergunta:
  - Recupera os trechos mais relevantes dos PDFs.
  - Monta o contexto.
  - Gera o prompt para o modelo.
  - Envia para o Ollama e exibe a resposta, citando as fontes.

### 4. **main**
- Lê argumentos da linha de comando (coleção, modelo, embedding, etc).
- Inicia o loop de chat.

O script permite conversar com um assistente que responde usando informações extraídas dos PDFs indexados, citando as fontes dos trechos usados. Ideal para buscas semânticas e perguntas sobre documentos.