from pathlib import Path
import re

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.agent import run_agent
from app.config import settings
from app.observability import configure_logging, request_log_middleware
from app.rag import ingest_documents, knowledge_status, reset_vector_store
from app.schemas import (
    ChatRequest,
    ChatResponse,
    IngestRequest,
    IngestResponse,
    ModelSettingsUpdate,
)
from app.security import require_admin
from app.settings_store import current_settings, update_runtime_settings


configure_logging()

app = FastAPI(title=settings.app_name)
app.middleware("http")(request_log_middleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=settings.cors_origin_list != ["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _safe_filename(filename: str) -> str:
    name = Path(filename).name
    name = re.sub(r"[^\w.\-\u4e00-\u9fff ]+", "_", name).strip()
    if not name or Path(name).suffix.lower() not in {".txt", ".md", ".pdf", ".docx"}:
        raise HTTPException(status_code=400, detail="仅支持 txt / md / pdf / docx 文件。")
    return name


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ready")
def ready() -> dict[str, str]:
    settings.raw_data_dir.mkdir(parents=True, exist_ok=True)
    settings.chroma_dir.mkdir(parents=True, exist_ok=True)
    return {
        "status": "ready",
        "model_provider": settings.provider_name,
        "chat_model": settings.resolved_chat_model,
    }


@app.get("/settings")
def get_settings(_: None = Depends(require_admin)) -> dict:
    return current_settings()


@app.post("/settings")
def save_settings(
    payload: ModelSettingsUpdate, _: None = Depends(require_admin)
) -> dict:
    try:
        return update_runtime_settings(payload.model_dump(exclude_none=True))
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/knowledge/status")
def status(_: None = Depends(require_admin)) -> dict[str, int | str]:
    current = knowledge_status()
    return {
        "raw_documents": current.raw_documents,
        "vector_chunks": current.vector_chunks,
        "model_provider": settings.provider_name,
        "chat_model": settings.resolved_chat_model,
        "base_url": settings.resolved_base_url,
        "embedding_provider": current.embedding_provider,
        "embedding_model": settings.resolved_embedding_model,
        "vector_store": current.vector_store,
        "chroma_dir": current.chroma_dir,
    }


@app.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest, _: None = Depends(require_admin)) -> ChatResponse:
    answer, sources, tool_used = run_agent(payload.session_id, payload.message)
    return ChatResponse(answer=answer, sources=sources, tool_used=tool_used)


@app.post("/ingest", response_model=IngestResponse)
def ingest(
    payload: IngestRequest, _: None = Depends(require_admin)
) -> IngestResponse:
    try:
        result = ingest_documents(payload.path, reset=payload.reset)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return IngestResponse(
        status="success",
        documents=result.documents,
        chunks=result.chunks,
        message=f"入库完成，当前使用：{result.vector_store} / {result.embedding_provider} embedding",
    )


@app.post("/knowledge/reset")
def reset(_: None = Depends(require_admin)) -> dict[str, str]:
    try:
        reset_vector_store()
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"status": "success"}


@app.post("/upload")
async def upload(
    file: UploadFile = File(...), _: None = Depends(require_admin)
) -> dict[str, str | int]:
    filename = _safe_filename(file.filename or "")
    content = await file.read()
    max_bytes = settings.max_upload_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"文件过大，最大允许 {settings.max_upload_mb} MB。",
        )
    settings.raw_data_dir.mkdir(parents=True, exist_ok=True)
    target = settings.raw_data_dir / filename
    target.write_bytes(content)
    return {"status": "success", "filename": filename, "size": len(content)}


app.mount("/", StaticFiles(directory="web", html=True), name="web")
