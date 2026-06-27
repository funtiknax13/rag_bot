import hashlib
import logging
import os
from pathlib import Path

from langchain_chroma import Chroma
from langchain_community.document_loaders import Docx2txtLoader, PyPDFLoader, TextLoader
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)

DOCS_PATH = os.getenv("DOCS_PATH", "/app/docs")
CHROMA_PATH = os.getenv("CHROMA_PATH", "/app/data/chroma")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")

SUPPORTED = {".pdf", ".docx", ".txt", ".md"}

_splitter = RecursiveCharacterTextSplitter(
    chunk_size=int(os.getenv("CHUNK_SIZE", "300")),
    chunk_overlap=int(os.getenv("CHUNK_OVERLAP", "50")),
)


def _file_hash(path: str) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _load_file(path: str):
    ext = Path(path).suffix.lower()
    if ext == ".pdf":
        return PyPDFLoader(path).load()
    if ext == ".docx":
        return Docx2txtLoader(path).load()
    if ext in {".txt", ".md"}:
        return TextLoader(path, encoding="utf-8").load()
    return []


def _get_vectorstore() -> Chroma:
    embeddings = OllamaEmbeddings(model=EMBED_MODEL, base_url=OLLAMA_BASE_URL)
    return Chroma(
        collection_name="docs",
        embedding_function=embeddings,
        persist_directory=CHROMA_PATH,
    )


def _indexed_hashes(vectorstore: Chroma) -> dict[str, str]:
    try:
        result = vectorstore.get(include=["metadatas"])
        hashes: dict[str, str] = {}
        for meta in result["metadatas"]:
            if meta and "source" in meta and "file_hash" in meta:
                hashes[meta["source"]] = meta["file_hash"]
        return hashes
    except Exception:
        return {}


def index_docs():
    docs_path = Path(DOCS_PATH)
    docs_path.mkdir(parents=True, exist_ok=True)

    vectorstore = _get_vectorstore()
    indexed = _indexed_hashes(vectorstore)

    new_chunks = []
    for file in sorted(docs_path.rglob("*")):
        if file.suffix.lower() not in SUPPORTED:
            continue
        path_str = str(file)
        file_hash = _file_hash(path_str)
        if indexed.get(path_str) == file_hash:
            logger.info(f"Без изменений, пропускаем: {file.name}")
            continue
        logger.info(f"Индексируем: {file.name}")
        try:
            docs = _load_file(path_str)
            chunks = _splitter.split_documents(docs)
            for chunk in chunks:
                chunk.metadata["source"] = path_str
                chunk.metadata["file_hash"] = file_hash
            new_chunks.extend(chunks)
        except Exception as e:
            logger.error(f"Ошибка при загрузке {file.name}: {e}")

    if new_chunks:
        vectorstore.add_documents(new_chunks)
        logger.info(f"Добавлено {len(new_chunks)} чанков")
    else:
        logger.info("Новых файлов нет, индексация не нужна")
