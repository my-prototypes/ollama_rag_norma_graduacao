# 🧩 Ollama RAG Starter Kit (macOS)

Este kit cria um protótipo de **IA generativa local** com **RAG sobre PDFs** usando **Ollama** + **ChromaDB**.

## ✅ Requisitos
- macOS (Apple Silicon)
- Python 3.10+
- Homebrew
- [Ollama](https://ollama.com) instalado e rodando localmente

## 🚀 Passo a passo (rápido)
1) Instale o Ollama e inicie o serviço:
```bash
brew install ollama
ollama serve &
```

2) Baixe um modelo de chat e um de embeddings (recomendado):
```bash
# ollama pull qwen2.5:7b-instruct
ollama pull llama3.2:3b
ollama pull nomic-embed-text
# alternativos:
# ollama pull llama3:8b-instruct
# ollama pull snowflake-arctic-embed:latest
```

3) Crie um ambiente Python e instale dependências:
```bash
python3 -m venv .venv && source .venv/bin/activate
pip3 install -r requirements.txt
```

4) Coloque seus PDFs na pasta:
```
data/pdfs/
```

5) Ingestão (gera base vetorial persistente em `vectordb/`):
```bash
python3 scripts/ingest_pdfs.py --pdf-dir data/pdfs --collection docs
```

6) Chat com RAG:
```bash
python3 scripts/chat_rag.py --collection docs --model llama3.2:3b --embed nomic-embed-text
```

## 🧠 Notas de uso
- **Hardware**: seu Mac mini (16 GB RAM) roda bem modelos até ~7–9B quantizados; usar Ollama simplifica muito.
- **Contexto**: por padrão pedimos top-5 trechos dos PDFs.
- **Persistência**: ChromaDB fica em `vectordb/`, pode ser apagado e recriado quando quiser.

## 🔧 Variáveis de ambiente
Copie `.env.example` para `.env` e ajuste se necessário:
```
cp .env.example .env
```
- `OLLAMA_BASE_URL` (default: http://localhost:11434)

## 🧪 Dicas
- PDFs muito grandes: faça upload aos poucos e reingira, ou aumente `--chunk-size`/`--chunk-overlap` conforme a necessidade.
- Se quiser mais velocidade, teste modelos menores (ex.: `phi3:mini`).
- Para citações, o script mostra a origem (arquivo e índice do trecho).
- Documentação da API Ollama: https://github.com/ollama/ollama/blob/main/docs/api.md
---
