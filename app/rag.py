import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

RAG_DIR = Path(__file__).resolve().parent.parent / "data" / "rag"
PDF_DIR = RAG_DIR / "pdfs"
CHROMA_DIR = RAG_DIR / "chroma"
RAG_DIR.mkdir(parents=True, exist_ok=True)
PDF_DIR.mkdir(parents=True, exist_ok=True)
CHROMA_DIR.mkdir(parents=True, exist_ok=True)

_collection = None


def _get_collection():
    global _collection
    if _collection is not None:
        return _collection
    try:
        import chromadb

        coll = chromadb.PersistentClient(path=str(CHROMA_DIR)).get_or_create_collection(
            name="potager_docs",
            metadata={"hnsw:space": "cosine"},
        )
        _collection = coll
        return coll
    except ImportError:
        logger.warning("chromadb non installé")
        return None


def is_available() -> bool:
    try:
        import chromadb

        return True
    except ImportError:
        return False


def chunk_text(text: str, chunk_size: int = 800, overlap: int = 150) -> list[str]:
    words = text.split()
    chunks, start = [], 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk = " ".join(words[start:end])
        if chunk.strip():
            chunks.append(chunk)
        start += chunk_size - overlap
    return chunks


def ingest_pdf(filepath: str, doc_title: str = "") -> dict:
    if not is_available():
        return {"ok": False, "error": "chromadb non installé"}
    try:
        from pypdf import PdfReader

        reader = PdfReader(filepath)
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        if not text.strip():
            return {"ok": False, "error": "Aucun texte extrait (PDF scanné?)"}
        chunks = chunk_text(text)
        doc_id = Path(filepath).stem
        title = doc_title or doc_id
        coll = _get_collection()
        existing = coll.get(where={"source": doc_id})
        if existing["ids"]:
            coll.delete(ids=existing["ids"])
        ids = [f"{doc_id}_{i}" for i in range(len(chunks))]
        coll.add(
            documents=chunks,
            ids=ids,
            metadatas=[{"source": doc_id, "title": title}] * len(chunks),
        )
        return {"ok": True, "chunks": len(chunks), "title": title, "id": doc_id}
    except Exception as e:
        logger.exception("ingest error")
        return {"ok": False, "error": str(e)}


def list_docs() -> list[dict]:
    if not is_available():
        return []
    try:
        coll = _get_collection()
        if coll is None or coll.count() == 0:
            return []
        data = coll.get()
        seen = {}
        for meta in data["metadatas"]:
            sid = meta["source"]
            if sid not in seen:
                seen[sid] = {"id": sid, "title": meta.get("title", sid), "chunks": 0}
            seen[sid]["chunks"] += 1
        return list(seen.values())
    except Exception:
        return []


def delete_doc(doc_id: str) -> bool:
    if not is_available():
        return False
    try:
        coll = _get_collection()
        ids = coll.get(where={"source": doc_id})["ids"]
        if ids:
            coll.delete(ids=ids)
        return True
    except Exception:
        return False


def search(query: str, k: int = 5) -> list[dict]:
    if not is_available():
        return []
    try:
        coll = _get_collection()
        if coll is None or coll.count() == 0:
            return []
        results = coll.query(query_texts=[query], n_results=k)
        docs = []
        for i in range(len(results["documents"][0])):
            docs.append(
                {
                    "text": results["documents"][0][i],
                    "source": results["metadatas"][0][i].get("source", "?"),
                    "title": results["metadatas"][0][i].get("title", "?"),
                }
            )
        return docs
    except Exception as e:
        logger.warning(f"search error: {e}")
        return []


def get_context(query: str, k: int = 3) -> str:
    docs = search(query, k=k)
    if not docs:
        return ""
    parts = [f"[Source: {d['title']}]\n{d['text']}" for d in docs]
    return "\n\n---\n\n".join(parts)
