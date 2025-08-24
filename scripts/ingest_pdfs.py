#!/usr/bin/env python3
import os
import argparse
import math
import uuid
from pathlib import Path
from typing import List, Dict, Tuple
from tqdm import tqdm
from dotenv import load_dotenv
import requests

from pypdf import PdfReader
import chromadb
from chromadb.config import Settings

load_dotenv()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

def pdf_to_text_chunks(pdf_path: str, chunk_size: int = 1200, chunk_overlap: int = 200) -> List[Tuple[str, int]]:
    """Extrai texto do PDF e retorna lista de (chunk_text, chunk_index)."""
    reader = PdfReader(pdf_path)
    full_text = []
    for i, page in enumerate(reader.pages):
        try:
            full_text.append(page.extract_text() or "")
        except Exception:
            full_text.append("")
    text = "\n".join(full_text)

    # Simples chunk por caracteres (robusto e suficiente para protótipo)
    chunks = []
    start = 0
    idx = 0
    n = len(text)
    while start < n:
        end = min(n, start + chunk_size)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append((chunk, idx))
            idx += 1
        start += max(1, chunk_size - chunk_overlap)
    return chunks
 
def embed_texts(texts: List[str], embed_model: str) -> List[List[float]]:
    """Gera embeddings usando Ollama /api/embeddings."""
    url = f"{OLLAMA_BASE_URL}/api/embeddings"
    embs = []
    for t in texts:
        payload = {"model": embed_model, "prompt": t}
        try:
            resp = requests.post(url, json=payload, timeout=120)
            resp.raise_for_status()
            data = resp.json()
            if "embedding" in data:
                embs.append(data["embedding"])
            elif "data" in data and isinstance(data["data"], list) and "embedding" in data["data"][0]:
                embs.append(data["data"][0]["embedding"])
            else:
                print("⚠️ Resposta inesperada da API de embedding:", data)
                raise RuntimeError("Embedding não retornado para um trecho.")
        except Exception as e:
            print("❌ Erro ao gerar embedding para trecho:")
            print("Trecho:", t[:100], "...")
            print("Erro:", str(e))
            raise
    return embs

def main():
    ap = argparse.ArgumentParser(description="Ingestão de PDFs -> ChromaDB via Ollama Embeddings")
    ap.add_argument("--pdf-dir", required=True, help="Diretório com PDFs")
    ap.add_argument("--collection", required=True, help="Nome da coleção")
    ap.add_argument("--embed", default="nomic-embed-text", help="Modelo de embedding no Ollama")
    ap.add_argument("--db-path", default="vectordb", help="Diretório para ChromaDB persistente")
    ap.add_argument("--chunk-size", type=int, default=1200)
    ap.add_argument("--chunk-overlap", type=int, default=200)
    args = ap.parse_args()

    client = chromadb.PersistentClient(path=args.db_path, settings=Settings(allow_reset=False))
    col = client.get_or_create_collection(args.collection, metadata={"hnsw:space": "cosine"})

    pdf_dir = Path(args.pdf_dir)
    pdfs = sorted([p for p in pdf_dir.glob("*.pdf") if p.is_file()])
    if not pdfs:
        print(f"Nenhum PDF encontrado em {pdf_dir.resolve()}")
        return

    for pdf in pdfs:
        print(f"\nProcessando: {pdf.name}")
        chunks = pdf_to_text_chunks(str(pdf), chunk_size=args.chunk_size, chunk_overlap=args.chunk_overlap)
        if not chunks:
            print("  (sem texto extraído)")
            continue

        texts = [c[0] for c in chunks]
        ids = [f"{pdf.name}::chunk_{i}" for _, i in chunks]
        metadatas = [{"source": pdf.name, "chunk_index": i} for _, i in chunks]

        # Embeddings em lote simples
        embeddings = []
        for i in tqdm(range(0, len(texts), 8), desc="Embeddings"):
            batch = texts[i:i+8]
            batch_embs = embed_texts(batch, args.embed)
            embeddings.extend(batch_embs)

        col.add(documents=texts, embeddings=embeddings, ids=ids, metadatas=metadatas)
        print(f"  Inseridos {len(texts)} chunks.")

    print("\n✅ Ingestão concluída. Coleção:", args.collection)
    print("Base vetorial em:", os.path.abspath(args.db_path))

if __name__ == "__main__":
    main()
