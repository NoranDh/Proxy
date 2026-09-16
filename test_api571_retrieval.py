# test_api571_retrieval.py
from scripts.rag_faiss_client import _vectorstore

# Check what sources actually exist across all stored docs
all_sources = set()
for doc_id, doc in _vectorstore.docstore._dict.items():
    src = doc.metadata.get("source") if hasattr(doc, "metadata") else None
    all_sources.add(src)

print("All sources in docstore:", all_sources)
print("Total docs:", len(_vectorstore.docstore._dict))

# Sample an api571 doc if it exists
for doc_id, doc in _vectorstore.docstore._dict.items():
    if hasattr(doc, "metadata") and doc.metadata.get("source") == "api571":
        print("\nSample api571 doc found:")
        print("  name:", doc.metadata.get("name"))
        print("  content:", doc.page_content[:100])
        break