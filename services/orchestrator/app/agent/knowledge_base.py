"""
Knowledge base cho agent, dựng bằng LangChain TFIDFRetriever.

Dùng TF-IDF (scikit-learn dưới nền, qua langchain_community) thay vì embedding
model để demo chạy offline, không cần tải model từ HuggingFace. Khi cần nâng
cấp lên embedding thật (đa ngôn ngữ, ngữ nghĩa tốt hơn), chỉ cần thay hàm
`get_retriever()` bằng một `VectorStoreRetriever` khác (Qdrant + bge-m3/Titan) —
phần còn lại của agent (tools.py, graph.py) không cần đổi vì đều thao tác qua
interface `BaseRetriever` chung của LangChain.
"""
from functools import lru_cache

from langchain_community.retrievers import TFIDFRetriever
from langchain_core.documents import Document

from app.data.loader import get_store


@lru_cache
def get_retriever(k: int = 15) -> TFIDFRetriever:
    store = get_store()
    docs = [
        Document(
            page_content=doc["content_vi"],
            metadata={
                "document_id": doc["document_id"],
                "title": doc["title"],
                "department": doc["department"],
                "classification": doc["classification"],
            },
        )
        for doc in store.list_documents()
    ]
    # k lớn hơn nhu cầu thật vì sẽ lọc bớt theo ACL ở tools.py ngay sau đó
    return TFIDFRetriever.from_documents(docs, k=k)
