from typing import List, Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    session_id: str = Field(default="default", min_length=1)
    message: str = Field(..., min_length=1)


class ChatResponse(BaseModel):
    answer: str
    sources: List[str] = []
    tool_used: Optional[str] = None


class IngestRequest(BaseModel):
    path: str = "./data/raw"
    reset: bool = True


class IngestResponse(BaseModel):
    status: str
    documents: int
    chunks: int
    message: str = ""


class ModelSettingsUpdate(BaseModel):
    model_provider: str
    api_key: Optional[str] = None
    base_url: str = ""
    chat_model: str = ""
    embedding_provider: str = "auto"
    embedding_api_key: Optional[str] = None
    embedding_base_url: str = ""
    embedding_model: str = ""
