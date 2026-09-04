from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class ProjectCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str = ""


class ProjectOut(BaseModel):
    id: str
    name: str
    description: str
    genre: Optional[str]
    status: str
    mode: str
    progress_pct: float
    version: int
    engine_target: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ChatMessageRequest(BaseModel):
    content: str = Field(min_length=1, max_length=4000)


class MessageOut(BaseModel):
    id: str
    role: str
    content: str
    message_type: str
    extra_data: dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True


class TaskOut(BaseModel):
    id: str
    code: str
    title: str
    description: str
    priority: int
    status: str
    depends_on: list
    related_files: list

    class Config:
        from_attributes = True


class AssetOut(BaseModel):
    id: str
    name: str
    asset_type: str
    file_path: str
    width: Optional[int]
    height: Optional[int]
    version: int
    provider_used: str

    class Config:
        from_attributes = True