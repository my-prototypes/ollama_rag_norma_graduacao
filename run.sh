#!/usr/bin/env bash
set -e

# 1) Start Ollama service
pgrep -x ollama >/dev/null || (echo 'Starting ollama serve...' && ollama serve & sleep 2)

# 2) Pull models
echo 'Pulling models...'
ollama pull llama3.2:3b || true
ollama pull nomic-embed-text || true

# 3) Python env
python3 -m venv .venv && source .venv/bin/activate
pip3 install -r requirements.txt

# 4) Ingest example (if any PDFs exist)
if ls data/pdfs/*.pdf 1> /dev/null 2>&1; then
  echo 'Ingesting PDFs...'
  python3 scripts/ingest_pdfs.py --pdf-dir data/pdfs --collection docs
else
  echo 'No PDFs found in data/pdfs. Add PDFs and run ingest manually.'
fi

# 5) Start chat
python3 scripts/chat_rag.py --collection docs --model llama3.2:3b --embed nomic-embed-text
