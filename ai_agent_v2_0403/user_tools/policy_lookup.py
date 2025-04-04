from langchain_core.tools import tool
import re
import numpy as np
from sentence_transformers import SentenceTransformer

doc_path = 'docs/general_faq.txt'
model = SentenceTransformer("all-mpnet-base-v2")

class VectorStoreRetriever:
    def __init__(self, docs: list, vectors: list):
        self._docs = docs
        self._arr = np.array(vectors)

    @classmethod
    def from_docs(cls, docs: list):
        text_list = [doc["page_content"] for doc in docs]
        vectors = model.encode(text_list)
        return cls(docs, vectors)

    def query(self, query: str, k: int = 5) -> list[dict]:
        query_vector = model.encode([query])[0]
        query_norm = np.linalg.norm(query_vector)
        doc_norms = np.linalg.norm(self._arr, axis=1)
        scores = (query_vector @ self._arr.T) / ((query_norm * doc_norms) + 1e-8)
        top_k_idx = np.argpartition(scores, -k)[-k:]
        top_k_idx_sorted = top_k_idx[np.argsort(-scores[top_k_idx])]
        return [
            {**self._docs[idx], "similarity": float(scores[idx])}
            for idx in top_k_idx_sorted
        ]

# Load documents from file
with open(doc_path, "r", encoding="utf-8") as file:
    faq_text = file.read()

docs = [{"page_content": txt.strip()} for txt in re.split(r"(?=\n\d+\. )", faq_text) if txt.strip()]
retriever = VectorStoreRetriever.from_docs(docs)

@tool
def pet_relocation_answer(query: str) -> str:
    """Consult the pet travel policies to answer user queries.
    Use this before directing users to external resources."""
    docs = retriever.query(query, k=2)
    return "\n\n".join([doc["page_content"] for doc in docs])