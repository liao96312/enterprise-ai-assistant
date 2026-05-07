from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
import re
import shutil
from pathlib import Path
from typing import Iterable, List

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import settings


SUPPORTED_SUFFIXES = {".txt", ".md", ".pdf", ".docx"}


@dataclass
class SourceChunk:
    content: str
    source: str


@dataclass
class IngestResult:
    documents: int
    chunks: int
    used_vector_store: bool
    embedding_provider: str
    vector_store: str


@dataclass
class KnowledgeStatus:
    raw_documents: int
    vector_chunks: int
    embedding_provider: str
    vector_store: str
    chroma_dir: str


class LocalHashEmbeddings(Embeddings):
    """Small deterministic embedding for demos without a remote embedding API."""

    def __init__(self, dimensions: int = 384) -> None:
        self.dimensions = dimensions

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self._embed(text) for text in texts]

    def embed_query(self, text: str) -> List[float]:
        return self._embed(text)

    def _embed(self, text: str) -> List[float]:
        vector = [0.0] * self.dimensions
        tokens = self._tokens(text)
        if not tokens:
            return vector

        for token in tokens:
            digest = hashlib.md5(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimensions
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[index] += sign

        norm = math.sqrt(sum(value * value for value in vector))
        if norm:
            vector = [value / norm for value in vector]
        return vector

    def _tokens(self, text: str) -> List[str]:
        lowered = text.lower()
        words = re.findall(r"[a-z0-9_]+", lowered)
        cjk = re.findall(r"[\u4e00-\u9fff]", lowered)
        return words + cjk


class LocalJsonVectorStore:
    """Persistent vector store fallback for local development."""

    def __init__(self, embedding_function: Embeddings) -> None:
        self.embedding_function = embedding_function
        self.path = settings.chroma_dir / "local_vector_store.json"
        self.items = self._load()

    def add_documents(self, documents: List[Document]) -> None:
        texts = [document.page_content for document in documents]
        vectors = self.embedding_function.embed_documents(texts)
        for document, vector in zip(documents, vectors):
            self.items.append(
                {
                    "content": document.page_content,
                    "metadata": document.metadata,
                    "vector": vector,
                }
            )
        self.persist()

    def similarity_search(self, query: str, k: int = 4) -> List[Document]:
        query_vector = self.embedding_function.embed_query(query)
        ranked = sorted(
            self.items,
            key=lambda item: self._cosine(query_vector, item["vector"]),
            reverse=True,
        )
        return [
            Document(page_content=item["content"], metadata=item.get("metadata", {}))
            for item in ranked[:k]
        ]

    def persist(self) -> None:
        settings.chroma_dir.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(self.items, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def count(self) -> int:
        return len(self.items)

    def _load(self) -> List[dict]:
        if not self.path.exists():
            return []
        return json.loads(self.path.read_text(encoding="utf-8"))

    def _cosine(self, left: List[float], right: List[float]) -> float:
        return sum(a * b for a, b in zip(left, right))


def _iter_source_files(base_dir: Path) -> Iterable[Path]:
    if not base_dir.exists():
        return []
    return (
        path
        for path in base_dir.rglob("*")
        if path.is_file() and path.suffix.lower() in SUPPORTED_SUFFIXES
    )


def _load_document(path: Path) -> List[Document]:
    suffix = path.suffix.lower()
    if suffix in {".txt", ".md"}:
        from langchain_community.document_loaders import TextLoader

        try:
            return TextLoader(str(path), encoding="utf-8").load()
        except UnicodeDecodeError:
            return TextLoader(str(path), encoding="gb18030").load()

    if suffix == ".pdf":
        from langchain_community.document_loaders import PyPDFLoader

        return PyPDFLoader(str(path)).load()

    if suffix == ".docx":
        from langchain_community.document_loaders import Docx2txtLoader

        return Docx2txtLoader(str(path)).load()

    return []


def _load_documents(base_dir: Path) -> List[Document]:
    documents: List[Document] = []
    for path in _iter_source_files(base_dir):
        for document in _load_document(path):
            document.metadata["source"] = path.name
            documents.append(document)
    return documents


def _split_documents(documents: List[Document]) -> List[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        separators=["\n\n", "\n", "。", "！", "？", ".", " ", ""],
    )
    return splitter.split_documents(documents)


def _embedding_provider_name() -> str:
    provider = settings.embedding_provider.lower()
    if provider == "auto":
        return "api" if settings.has_api_embedding_config else "local"
    if provider in {"api", "openai", "local"}:
        if provider == "openai":
            return "api"
        return provider
    raise RuntimeError("EMBEDDING_PROVIDER must be auto, api, openai, or local.")


def _embedding_function() -> Embeddings:
    provider = _embedding_provider_name()
    if provider == "local":
        return LocalHashEmbeddings(settings.local_embedding_dimensions)

    if not settings.resolved_embedding_api_key:
        raise RuntimeError("EMBEDDING_API_KEY or API_KEY is required when EMBEDDING_PROVIDER=api.")

    from langchain_openai import OpenAIEmbeddings

    kwargs = {
        "api_key": settings.resolved_embedding_api_key,
        "model": settings.resolved_embedding_model,
    }
    if settings.resolved_embedding_base_url:
        kwargs["base_url"] = settings.resolved_embedding_base_url
    return OpenAIEmbeddings(**kwargs)


def _chroma_class():
    try:
        from langchain_chroma import Chroma

        return Chroma
    except ImportError:
        from langchain_community.vectorstores import Chroma

        return Chroma


def _vector_store():
    embedding = _embedding_function()
    try:
        Chroma = _chroma_class()
        return Chroma(
            collection_name=settings.chroma_collection_name,
            persist_directory=str(settings.chroma_dir),
            embedding_function=embedding,
        )
    except ImportError:
        return LocalJsonVectorStore(embedding)


def _vector_store_name(store: object | None = None) -> str:
    if isinstance(store, LocalJsonVectorStore):
        return "local_json"
    return "chroma"


def reset_vector_store() -> None:
    resolved = settings.chroma_dir.resolve()
    workspace = Path.cwd().resolve()
    if workspace not in resolved.parents and resolved != workspace:
        raise RuntimeError("Refusing to delete a vector store outside the workspace.")
    if settings.chroma_dir.exists():
        shutil.rmtree(settings.chroma_dir)


def ingest_documents(path: str | Path, reset: bool = False) -> IngestResult:
    if reset:
        reset_vector_store()

    base_dir = Path(path)
    documents = _load_documents(base_dir)
    chunks = _split_documents(documents)

    settings.chroma_dir.mkdir(parents=True, exist_ok=True)
    store = _vector_store()
    if chunks:
        store.add_documents(chunks)
        persist = getattr(store, "persist", None)
        if callable(persist):
            persist()

    return IngestResult(
        documents=len(documents),
        chunks=len(chunks),
        used_vector_store=True,
        embedding_provider=_embedding_provider_name(),
        vector_store=_vector_store_name(store),
    )


def knowledge_search(query: str, top_k: int | None = None) -> List[SourceChunk]:
    limit = top_k or settings.top_k
    store = _vector_store()
    docs = store.similarity_search(query, k=limit)
    return [
        SourceChunk(
            content=doc.page_content,
            source=str(doc.metadata.get("source", "unknown")),
        )
        for doc in docs
    ]


def knowledge_status() -> KnowledgeStatus:
    raw_documents = len(list(_iter_source_files(settings.raw_data_dir)))
    vector_chunks = 0
    if settings.chroma_dir.exists():
        try:
            store = _vector_store()
            if isinstance(store, LocalJsonVectorStore):
                vector_chunks = store.count()
            else:
                vector_chunks = int(store._collection.count())
        except Exception:
            vector_chunks = 0

    return KnowledgeStatus(
        raw_documents=raw_documents,
        vector_chunks=vector_chunks,
        embedding_provider=_embedding_provider_name(),
        vector_store=_vector_store_name(_vector_store() if settings.chroma_dir.exists() else None),
        chroma_dir=str(settings.chroma_dir),
    )
