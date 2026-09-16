from pathlib import Path 
from langchain_huggingface import HuggingFaceEmbeddings 
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
import json 

BASE_DIR = Path(__file__).resolve().parents[1]
API571_PATH = BASE_DIR / "data" / "api571_mechanisms_clean.json"
INDEX_DIR = BASE_DIR / "data" / "rag_faiss_index"
EMB_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

embedding = HuggingFaceEmbeddings(model_name = EMB_MODEL_NAME)

def build_api571_docs() -> list[Document]:
    with open(API571_PATH, encoding="utf-8", errors="ignore") as f:
        entries = json.load(f)

    print(f"  Loaded {len(entries)} entries from JSON")

    docs = []
    for entry in entries:
        # Combine the most semantically similar fields into one searchable text
        # the text (page content in the doc variable) is embeded
        text = "\n".join(filter(
            None, [
                entry.get("name", ""),
                entry.get("description", ""),
                entry.get("summary", ""),
                " ".join(entry.get("critical factors", []))[:500]
            ]))
        # store the fileds in metadata (not embedded)
        doc = Document(
            page_content=text,
            metadata={
                "source": "api571",
                "id": entry.get("id"),
                "section": entry.get("section"),
                "name": entry.get("name"),
                "prevention_mitigation": entry.get("prevention_mitigation", []),
                "inspection_monitoring": entry.get("inspection_monitoring", []),
            }
        )
        docs.append(doc)
    print(f"  Built {len(docs)} documents")
    return docs

def main():
    print("Building API 571 documents...")
    api571_docs = build_api571_docs()
    print(f"  {len(api571_docs)} entries to add")

    print("Loading existing FAISS index...")
    existing = FAISS.load_local(
        folder_path=str(INDEX_DIR),
        embeddings=embedding,
        allow_dangerous_deserialization=True
    )

    # Extract existing docs from docstore
    print("Extracting existing documents...")
    existing_docs = list(existing.docstore._dict.values())
    print(f"  {len(existing_docs)} existing docs found")

    # Combine all docs
    all_docs = existing_docs + api571_docs
    print(f"  Total: {len(all_docs)} documents")

    # Rebuild index from scratch with all docs
    print("Rebuilding FAISS index from scratch...")
    new_vectorstore = FAISS.from_documents(all_docs, embedding)

    print("Saving...")
    new_vectorstore.save_local(str(INDEX_DIR))
    print(f"Done. Index rebuilt at {INDEX_DIR}")

if __name__ == "__main__":
    main()