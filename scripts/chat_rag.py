import os
import argparse
from typing import List, Dict, Any
from dotenv import load_dotenv
import requests
import chromadb
from chromadb.config import Settings

load_dotenv()
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

#SYSTEM_PROMPT = """Você é um assistente útil que responde em PT-BR.
#Use APENAS as informações relevantes do CONTEXTO quando a pergunta for sobre os PDFs.
#Se a resposta não estiver no contexto, seja transparente e indique o que você sabe sem alucinar.
#Mostre no final as fontes (arquivo e índice do trecho)."""

SYSTEM_PROMPT = """
Você é um assistente universitário da UFPI especializado em responder PERGUNTAS SOBRE AS NORMAS DE GRADUAÇÃO.
REGRAS OBRIGATÓRIAS:
1) Responda SOMENTE com base no CONTEXTO fornecido (trechos dos PDFs oficiais).
2) Se a resposta NÃO estiver no contexto, diga claramente: "Não encontrei a resposta nos PDFs fornecidos."
3) Ao responder, cite a(s) seção(ões), artigo(s) ou página(s) quando disponíveis no contexto.
4) Seja conciso, claro e objetivo. Liste passos quando for um procedimento.
5) Não invente nomes, números de artigos, prazos ou exceções que não estejam explicitamente no CONTEXTO.
"""

TEMPLATE = """[SISTEMA]
{system}

[CONTEXTO]
{context}

[USUÁRIO]
{query}

[INSTRUÇÕES]
- Seja conciso e objetivo.
- Se citar números ou fatos, tente confirmar no CONTEXTO.
- No final, liste as fontes como: (Fonte: arquivo#chunk_index).
"""

def ollama_chat(model: str, messages: List[Dict[str, str]], stream: bool = False) -> str:
    url = f"{OLLAMA_BASE_URL}/api/chat"
    payload = {"model": model, "messages": messages, "stream": stream}
    r = requests.post(url, json=payload, timeout=120)
    r.raise_for_status()
    data = r.json()
    if stream:
        # Este exemplo não faz streaming; mantemos simples
        pass
    # compatível com /api/chat do Ollama
    content = data.get("message", {}).get("content")
    if not content and "choices" in data:
        content = data["choices"][0]["message"]["content"]
    return content or ""
 
def embed_text(text: str, embed_model: str) -> List[float]:
    url = f"{OLLAMA_BASE_URL}/api/embeddings"
    payload = {"model": embed_model, "prompt": text}
    try:
        r = requests.post(url, json=payload, timeout=60)
        r.raise_for_status()
        data = r.json()
        if "embedding" in data:
            return data["embedding"]
        elif "data" in data and isinstance(data["data"], list) and "embedding" in data["data"][0]:
            return data["data"][0]["embedding"]
        else:
            print("⚠️ Resposta inesperada da API:", data)
            raise RuntimeError("Embedding não retornado corretamente.")
    except Exception as e:
        print(f"❌ Erro ao gerar embedding: {e}")
        raise RuntimeError("Falha ao obter embedding do Ollama.") from e

def retrieve(query: str, collection: str, db_path: str, embed_model: str, k: int = 5) -> List[Dict[str, Any]]:
    client = chromadb.PersistentClient(path=db_path, settings=Settings(allow_reset=False))
    col = client.get_or_create_collection(collection, metadata={"hnsw:space": "cosine"})
    qvec = embed_text(query, embed_model)
    res = col.query(query_embeddings=[qvec], n_results=k, include=["documents", "metadatas", "distances", "embeddings"])
    docs = []
    if res and res.get("documents"):
        for doc, meta, dist in zip(res["documents"][0], res["metadatas"][0], res["distances"][0]):
            docs.append({"text": doc, "meta": meta, "score": 1.0 - dist})
    return docs

def build_context(docs: List[Dict[str, Any]]) -> str:
    parts = []
    for d in docs:
        src = d["meta"].get("source")
        idx = d["meta"].get("chunk_index")
        parts.append(f"[{src}#chunk_{idx}]\n{d['text']}\n")
    return "\n---\n".join(parts)

def chat_loop(args):
    print("🔎 Coleção:", args.collection, "| Modelo:", args.model, "| Embed:", args.embed)
    print("Digite sua pergunta (ou 'sair'):\n")
    while True:
        try:
            q = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nSaindo.")
            break
        if not q:
            continue
        if q.lower() in {"sair", "exit", "quit"}:
            break

        docs = retrieve(q, args.collection, args.db_path, args.embed, k=args.k)
        context = build_context(docs) if docs else "(sem resultados relevantes)"
        srcs = ", ".join([f"{d['meta'].get('source')}#chunk_{d['meta'].get('chunk_index')}" for d in docs]) or "N/A"

        prompt = TEMPLATE.format(system=SYSTEM_PROMPT, context=context, query=q)
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        answer = ollama_chat(args.model, messages, stream=False)

        print("\n" + "="*80)
        print(answer.strip())
        print(f"\n(Fonte: {srcs})")
        print("="*80 + "\n")

def main():
    ap = argparse.ArgumentParser(description="Chat com RAG (Ollama + ChromaDB)")
    ap.add_argument("--collection", required=True, help="Nome da coleção (mesmo usado na ingestão)")
    ap.add_argument("--model", default="llama3.2:3b", help="Modelo de chat no Ollama")
    ap.add_argument("--embed", default="nomic-embed-text", help="Modelo de embedding no Ollama")
    ap.add_argument("--db-path", default="vectordb", help="Diretório de persistência do ChromaDB")
    ap.add_argument("--k", type=int, default=5, help="Top-k documentos para o contexto")
    args = ap.parse_args()
    chat_loop(args)

if __name__ == "__main__":
    main()