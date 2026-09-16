# rag/store.py
from pathlib import Path
import json, pickle
from sentence_transformers import SentenceTransformer
from sklearn.neighbors import NearestNeighbors
import numpy as np

DATA_DIR = Path("data")
CORPUS_FILE = DATA_DIR / "rag_corpus.jsonl"
INDEX_FILE = DATA_DIR / "rag_index.pkl" #pickle file 

print("Loading embedding model...")
model = SentenceTransformer("multi-qa-mpnet-base-dot-v1")  


def embed(text: str):
    """Return a 768-dim embedding from local model."""
    return model.encode(text, normalize_embeddings=True)

_EMB_MODEL_NAME = "BAAI/bge-large-en-v1.5"  # or whatever you used
_embedder = SentenceTransformer(_EMB_MODEL_NAME)

_store_cache = None  # lazy-load


def load_store():
    """Load pickled RAG store (chunks + embeddings + NN index)."""
    global _store_cache
    if _store_cache is None:
        with INDEX_FILE.open("rb") as f:
            _store_cache = pickle.load(f)
    return _store_cache


def retrieve_chunks(query_text: str, top_k: int = 6) -> list[dict]:
    """
    Given a text query, return top_k most similar chunks
    from case studies + handbook.
    """
    store = load_store()
    rows = store["rows"]
    nn = 5          # sklearn NearestNeighbors   NEVER BEEN USED! 
    # embed query
    q_vec = _embedder.encode([query_text], normalize_embeddings=True) # embedding user query 
    distances, indices = nn.kneighbors(q_vec, n_neighbors=top_k)

    hits = []
    for idx in indices[0]:
        hits.append(rows[int(idx)])
    return hits

# ---------- 3. MAIN: BUILD INDEX ----------
def main():
    print("Loading corpus...")
    rows = []
    with CORPUS_FILE.open("r", encoding="utf-8") as f:
        for line in f:
            rows.append(json.loads(line))

    print(f"Embedding {len(rows)} chunks...")

    embeddings = []
    for r in rows:
        emb = embed(r["text"])
        embeddings.append(emb)

    embeddings = np.array(embeddings)

    # Build kNN index
    print("Building index...")
    knn = NearestNeighbors(n_neighbors=5, metric="cosine")
    knn.fit(embeddings)

    # Save everything
    with INDEX_FILE.open("wb") as f:
        pickle.dump({"rows": rows, "embeddings": embeddings, "index": knn}, f)

    print(f"Index saved → {INDEX_FILE}")




if __name__ == "__main__":
    main()