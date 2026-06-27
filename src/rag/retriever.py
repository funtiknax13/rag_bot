import os

from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings

CHROMA_PATH = os.getenv("CHROMA_PATH", "/app/data/chroma")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
TOP_K = int(os.getenv("TOP_K", "5"))

_vectorstore: Chroma | None = None


def get_vectorstore() -> Chroma:
    global _vectorstore
    if _vectorstore is None:
        embeddings = OllamaEmbeddings(model=EMBED_MODEL, base_url=OLLAMA_BASE_URL)
        _vectorstore = Chroma(
            collection_name="docs",
            embedding_function=embeddings,
            persist_directory=CHROMA_PATH,
        )
    return _vectorstore


def retrieve(query: str) -> list[str]:
    docs = get_vectorstore().similarity_search(query, k=TOP_K)
    return [doc.page_content for doc in docs]
